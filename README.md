# Orchestrate
Orchestrate lets you manage multiple Docker-based services via docker-compose.

## What is this?
Orchestrate was written to control docker-compose services easily and give each service its own IP address through macvlan networking. This makes each service easy to access without having to manually expose ports. It's less secure to expose each service directly to the network without a firewall, but this is intended for already-secure internal networks. If a service needs a firewall, it's fairly easy to whip up an Alpine / iptables container. More detail on this coming soon (TM).

## Usage
```
$ ./orchestrate.py --help
usage: orchestrate.py [-h] [--config CONFIG]
                      {start,stop,restart,status,shell} ... service

positional arguments:
  service               which service(s) to act on (a list in the form a,b,c
                        or 'all')

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        location of the config file (default is ./config.yml)

action:
  {start,stop,restart,status,shell}
    start               start the service(s)
    stop                stop the service(s)
    restart             restart the service(s)
    status              get the status of the service(s)
    shell               enter the shell of a service's container (you will be
                        prompted if there are multiple)
```

### Prerequisites
- Python 3.5+
    - [Python Docker API](https://pypi.python.org/pypi/docker/)
    - [PyYAML](https://github.com/yaml/pyyaml)
- Docker Community Edition
    - docker-compose
- Currently orchestrate.py must be run on the target machine by a user who is a member of the `docker` group. If you need remote capabilities (TLS), open an issue and I'll implement it.

### Basic operations
Start a service (latest version of image:tag will be pulled automatically):
```sh
./orchestrate.py start service1
```

Start several services:
```sh
./orchestrate.py start service1,service2,service3
```

Stop a service:
```sh
$ ./orchestrate.py stop deluge

Reclaimed 0.0MB
Applying action 'stop' to the following services: 'deluge'
Stopping deluge
Stopping deluge ... done
Stopping vpn    ... done
Removing deluge ... done
Removing vpn    ... done
Network external-network is external, skipping
```

Access the shell of a service:
```sh
$ ./orchestrate.py shell deluge

Reclaimed 83MB
Applying action 'shell' to the following services: 'deluge'
Multiple containers running, select from the following:
0 : Exit
1 : deluge
2 : vpn
> 1
Entering container deluge
root@6dcc3073e2ab:/$ ls
app  config    dev        etc   init  libexec  mnt   root  sbin  sys  usr
bin  defaults  downloads  home  lib   media    proc  run   srv   tmp  var
```

## Configuration
### Directory structure
All this should be within the `base-directory` specified in `config.yml`. A full example can be seen in `/example`.

```
|-- orchestrate.py
|-- config.yml
|--| service1
   |-- docker-compose.yml
   |-- service1-file
|--| service2
   |-- docker-compose.yml
|--| service3
   |-- docker-compose.yml
   |-- servce3-example-file
```

You will also need a data directory for each service. This can be within the service folder or separately:

```
|--| service1
   |-- service1.container1.conf
   |-- service1.container3.yml
|--| service2
   |-- service2.container5.env
```

### Sample configuration file
The below will have each container assigned an IP address in the range 192.168.0.2–192.168.0.254

```yaml
base-directory: /services      # Directory containing orchestrate.py, config.yml and subdirectories for each service
shutdown-timeout: 20           # Timeout when shutting down containers
prune: true                    # Whether to delete old containers, images and volumes
macvlan-network:
  name: "external-network"     # The name of the macvlan network that is shared between all services
  subnet: "255.255.255.0"      # Network subnet
  gateway: "192.168.0.1"       # Network gateway (usually your router's IP address)
  parent: eth0                 # Parent interface (usually eth0, check with `ip addr`)
```

### Networking
In each the `docker-compose.yml` file for each container that you wish to connect to the external network you need to add the following:

```yaml
...
services:
  mycontainer:
    networks:
      default:
        ipv4_address:
          192.168.0.4
...
```

And at the bottom of the file:

```yaml
networks:
  default:
    external:
      name: external-network
```
