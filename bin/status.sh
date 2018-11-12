#!/usr/bin/env bash

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

echo
echo OPC-UA Converter Core Services:
echo
echo [opcua_converter] $(pgrep -f 'opcua_converter.py')
echo
echo [opcua_plugins]:
pgrep -f -a 'pymodules/loader.py' | gawk '{ print $1, $4}'
echo
echo [rabbitmq-server] $(pgrep -f 'rabbitmq-server')
echo
echo For MQTT Plugin:
echo [mosquitto] $(pgrep -f 'mosquitto')
echo
