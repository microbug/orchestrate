# Orchestrate
Orchestrate lets you manage multiple Docker-based services via docker-compose.

## What is this?
Orchestrate was written to control docker-compose services easily and give each service its own IP address through macvlan networking. This makes each service easy to access without worrying about exposing ports. Of course, it's less secure to expose each service directly to the network without a firewall, but this is intended for already-secure networks. If a service needs a firewall, it's fairly easy to whip up an Alpine / iptables container. More detail on this coming soon.

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

### Sample configuration file
The below will have each container assigned an IP address in the range 192.168.0.2–192.168.0.254

```yaml
base-directory: /services      # Directory containing orchestrate.py, config.yml and subdirectories for each service
shutdown-timeout: 20           # Timeout when shutting down containers
prune: true                    # Whether to delete old containers, images and volumes
macvlan-network:
  name: "microbug.uk-internal" # The name of the macvlan network that is shared between all services
  subnet: "255.255.255.0"      # Network subnet
  gateway: "192.168.0.1"       # Network gateway (usually your router's IP address)
  parent: eth0                 # Parent interface (usually eth0, check with `ip addr`)
```

### Sample docker-compose.yml