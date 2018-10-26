#!/bin/sh
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

make
cd common/rabbitmq-c
mv librabbitmq /tmp/
mv build /tmp/
rm -rf *
mv /tmp/librabbitmq .
find ./ -name "*.c" | xargs rm
mkdir build
mv /tmp/build/librabbitmq build/
rm -rf /tmp/build

cd ../json-c/
find ./ -name "*.c" | xargs rm
cd ../
git apply ./0001-kw-make-file-for-kw-scan.patch
cd ../
rm -rf ~/kw/kwtables/opcua_converter-sdk/*
make clean
kwinject make
kwbuildproject --url http://localhost:8080/opcua_converter-sdk -o ~/kw/kwtables/opcua_converter-sdk kwinject.out
kwadmin --url http://localhost:8080/ load opcua_converter-sdk ~/kw/kwtables/opcua_converter-sdk/




