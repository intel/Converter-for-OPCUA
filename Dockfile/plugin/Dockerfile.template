# Copyright (c) 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM ubuntu:xenial 
ENV HOSTNAME=opcua
ARG http_proxy
ARG https_proxy
ENV http_proxy=${http_proxy}
ENV https_proxy=${https_proxy}

WORKDIR /root/
RUN apt-get -y update
RUN apt-get install -y dialog apt-utils software-properties-common
RUN add-apt-repository ppa:mosquitto-dev/mosquitto-ppa
RUN apt-get -y update
RUN apt-get install -y --fix-broken \
    python3.5 \
    curl \
    zip  \
    vim \
    git \
    gawk

RUN apt-get install -y python3-pip python-pip
RUN pip3 install enum34==1.1.6
RUN pip3 install trollius==2.2
RUN pip3 install dateutils==0.6.6
RUN pip3 --default-timeout=100 install opcua==0.90.4
RUN pip3 install amqpstorm==2.4.0
RUN pip3 install cryptography==2.1.4
RUN pip install supervisor==3.3.4

# CUSTOMIZE: add relate plugin dependence apt package to here, e.g. "RUN apt-get install -y --fix-broken <dependence package>"

# CUSTOMIZE: add relate plugin dependence pip package to here, e.g. "RUN pip3 install <dependence package>==<specify version>"

# CUSTOMIZE: copy relate plugin code to here, e.g. "COPY <code folder> /root/"


COPY entrypoint.sh /root/
COPY supervisord_plugin.conf /root/supervisord.conf
RUN mkdir /var/log/opcua/
RUN chmod +x /root/entrypoint.sh

# CUSTOMIZE: touch relate log file to avoid log file fail to create, e.g. "RUN touch /var/log/opcua/<plugin log file>"

ENTRYPOINT ["/root/entrypoint.sh"]

ONBUILD RUN rm -rf /root/*

WORKDIR /root/
