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
                        location of the config file

action:
  {start,stop,restart,status,shell}
    start               start the service(s)
    stop                stop the service(s)
    restart             restart the service(s)
    status              get the status of the service(s)
    shell               enter the shell of a service's container (you will be
                        prompted if there are multiple)
```
