# Using docker plugin template to build docker image How-To

## 1. Install docker-ce with ubuntu 16.04

please refer to [docker.io](https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-docker-ce-1)

## 2. See **Dockerfile.template** to create **Dockerfile** for specify plugin

**Dockerfile.template** provide a template to build specify plugin, It needs to add dependencies in the **CUSTOMIZE** sections

There are 4 **CUSTOMIZE** sections in **Dockerfile.template** as below, please refer to **Dockerfile.template** to create specify **Dockerfile** for your plugin, which will help you to build your docker image for your plugin

    # CUSTOMIZE: add relate plugin dependence apt package to here, e.g. "RUN apt-get install -y --fix-broken <dependence package>"

    # CUSTOMIZE: add relate plugin dependence pip package to here, e.g. "RUN pip3 install <dependence package>==<specify version>"

    # CUSTOMIZE: copy relate plugin code to here, e.g. "COPY <code folder> /root/"

    # CUSTOMIZE: touch relate log file to avoid log file fail to create, e.g. "RUN touch /var/log/opcua/<plugin log file>"

## 3. Using supervisord to manage plugin run with docker

please refer to `supervisord_plugin.conf`, two part need to modify, `[group:opcua]` to add program into running list, `[program:<program name>]` to add command and start/restart way.

Note: current conf is using modbus plugin as example

    ; The sample group section below shows all possible group values.  Create one
    ; or more 'real' group: sections to create "heterogeneous" process groups.

    [group:opcua]
    programs=modbus-plugin  ; each refers to 'x' in [program:x] definitions
    ;priority=999                  ; the relative start priority (default 999)

    [program:modbus-plugin]
    command=python3 pymodules/loader.py pymodules/pymodbus-tcp
    directory=/root/opcua_plugin/
    autostart=true
    autorestart=true
    stdout_logfile=/root/%(program_name)s.log
    stderr_logfile=/root/%(program_name)s.log

## 4. Build docker image with Dockerfile

use `docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -t cfsdk/modbus_plugin .` to build docker images, after successful, you will find **cfsdk/modbus_plugin** docker images with `docker images`

## 5. Run docker image
    $ docker run -h opcua -ti cfsdk/modbus_plugin bash

