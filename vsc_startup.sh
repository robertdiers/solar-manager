#! /bin/bash

# create required folders for vsc-server config
mkdir -p ~/.config

# start all containers and give user id
EXAMPLE_UID=${UID} EXAMPLE_GID=${GID} podman-compose -p vsc-solar-manager up --build --detach
