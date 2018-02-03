#!/usr/bin/env python3

import argparse
import docker
import os
import subprocess
import yaml

docker_client = docker.from_env()


def docker_compose_execute(service, commands, config, capture_stdout=False):
    """Execute a command in the docker-compose CLI
    Returns the subprocess.CompletedProcess object
    commands must be a list as it is concatenated to another list
    """
    # chdir to service's directory
    os.chdir(os.path.join(config["base-directory"], service))
    subprocess_args = ["docker-compose"] + commands
    stdout_arg = subprocess.PIPE if capture_stdout else False
    completed_process = subprocess.run(subprocess_args, stdout=stdout_arg)
    os.chdir(config["base-directory"])
    return completed_process


def start(services, config):
    """Pull the latest image(s) for a service and prune old ones, then start it
    """
    for service in services:
        # If service is already up it will not be restarted
        print("Updating image for " + service)
        docker_compose_execute(service, ["pull"], config)

        print("Starting " + service)
        docker_compose_execute(service, ["up", "-d", "--build", "-t",
                                         str(config["shutdown-timeout"]),
                                         "--no-recreate"], config)


def stop(services, config):
    for service in services:
        print("Stopping " + service)
        docker_compose_execute(service, ["stop", "-t",
                               str(config["shutdown-timeout"])], config)
        docker_compose_execute(service, ["down"], config)


def network_setup(name, subnet, gateway, parent, config):
    existing_networks = docker_client.networks.list()
    create_network = True
    for network in existing_networks:
        if network.name == name:
            return False

    ipam_pool = docker.types.IPAMPool(
        subnet=subnet,
        gateway=gateway
    )
    ipam_config = docker.types.IPAMConfig(
        pool_configs=[ipam_pool]
    )
    docker_client.networks.create(
        name,
        driver="macvlan",
        options={"parent": parent},
        ipam=ipam_config
    )

    return True


def status(services, config):
    for service in services:
        if len(services) > 1:
            print("\nShowing containers for " + service)
        docker_compose_execute(service, ["ps"], config)
        print("")  # newline


def verify_only_one_service(services):
    if len(services) > 1:
        print("! Error: this command only takes one service as an argument")
        print("! Exiting")
        exit(2)
    else:
        return services[0]


def shell(services, config):
    service = verify_only_one_service(services)

    proc = docker_compose_execute(service=service, commands=["ps", "-q"],
                                  config=config, capture_stdout=True)
    container_ids = proc.stdout.splitlines()
    for index, container_id in enumerate(container_ids):
        container_ids[index] = container_id.decode("ascii")

    if len(container_ids) == 0:
        print("No containers running! Exiting")
        exit(3)

    if len(container_ids) > 1:
        print("Multiple containers running, select from the following:")
        print("0 : Exit")
        for index, container_id in enumerate(container_ids):
            print(str(index+1) + " : " +
                  str(docker_client.containers.get(container_id).name))
        while True:
            response = input("> ")
            if response.isdigit():
                if int(response) <= len(container_ids):
                    response = int(response)
                    break
                else:
                    print(response + " is greater than the maximum number (" +
                          str(len(container_ids)) + ")")
            else:
                print(response + " is not an integer")
        if response == 0:
            print("Exiting")
            exit(0)
    else:
        response = 1

    container_id = container_ids[response-1]
    print("Entering container " +
          docker_client.containers.get(container_id).name)
    subprocess.run(["docker", "exec", "-it", container_id, "sh"])


def logs(services, config, no_follow):
    service = verify_only_one_service(services)

    commands = ["logs"]
    if no_follow is False:
        commands.append("-f")
    try:
        proc = docker_compose_execute(service=service, commands=commands,
                                      config=config)
    except KeyboardInterrupt:
        print("Keyboard interrupt caught, exiting")
        exit(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", default="config.yml", help="location of the config file (default is ./config.yml)")
    subparsers = parser.add_subparsers(title="action", dest="action")
    parser_start = subparsers.add_parser("start", help="start the service(s)")
    parser_stop = subparsers.add_parser("stop", help="stop the service(s)")
    parser_stop.add_argument("--force", "-f", action="store_true", help="force the service(s) to stop")
    parser_restart = subparsers.add_parser("restart", help="restart the service(s)")
    parser_restart.add_argument("--force", "-f", action="store_true", help="force the service(s) to stop before they are started again")
    parser_status = subparsers.add_parser("status", help="get the status of the service(s)")
    parser_shell = subparsers.add_parser("shell", help="enter the shell of a service's container (you will be prompted if there are multiple)")
    parser_logs = subparsers.add_parser("logs", help="follow the logs of a service")
    parser_logs.add_argument("--no-follow", "-n", action="store_true", help="print current logs but do not follow further output")
    parser.add_argument("service", help="which service(s) to act on (a list in the form a,b,c or 'all')")
    args = parser.parse_args()

    # chdir to directory containing manage.py
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    config = yaml.load(open(args.config, 'r'))

    network = config["macvlan-network"]
    network_setup(network["name"], network["subnet"], network["gateway"],
                  network["parent"], config)

    if config["prune"] is True:
        reclaimed_space = 0
        reclaimed_space += docker_client.images.prune()['SpaceReclaimed']
        reclaimed_space += docker_client.volumes.prune()['SpaceReclaimed']
        reclaimed_space += docker_client.containers.prune()['SpaceReclaimed']
        reclaimed_space /= 1e6
        print("Reclaimed {n}MB".format(n=reclaimed_space))

    services = []
    if args.service == "all":
        # List directories
        directories = filter(lambda x: os.path.isdir(os.path.join('.', x)),
                             os.listdir('.'))
        for directory in directories:
            if "docker-compose.yml" in os.listdir(directory):
                services.append(directory)
    else:
        services_raw = args.service.split(",")
        for service in services_raw:
            if os.path.isdir(os.path.join(".", service)):
                services.append(service)
            else:
                print("! Error: directory not found: " + service)
                print("! Exiting")
                exit(1)

    print("Applying action '{a}' to the following services: {s}"
          .format(a=args.action, s=str(services).strip("[]")))

    if args.action == "start":
        start(services, config)
    elif args.action == "stop":
        stop(services, config)
    elif args.action == "restart":
        stop(services, config)
        start(services, config)
    elif args.action == "status":
        status(services, config)
    elif args.action == "shell":
        shell(services, config)
    elif args.action == "logs":
        logs(services, config, args.no_follow)


if __name__ == "__main__":
    main()
