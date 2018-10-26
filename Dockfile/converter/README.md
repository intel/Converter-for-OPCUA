# Converter for OPC UA Docker How-To

## 1. Install docker-ce with ubuntu 16.04

please refer to [docker.io](https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-docker-ce-1)

## 2. Build docker image with Dockerfile

use `docker build --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -t cfsdk/converter .` to build docker images, after successful, you will find **cfsdk/converter** docker images with `docker images`

## 3. Run docker image
    $ docker run -h opcua -p 4840:4840 -p 5672:5672 -ti cfsdk/converter bash
