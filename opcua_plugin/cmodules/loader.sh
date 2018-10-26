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

usage="$(basename "$0") <plugin folder>"

if [ $# -ge 2 ]; then
  echo "$usage"
  exit
fi

folder=$1
name=${folder#*/}
for json in `ls $folder/*.json`; do
  kill $(ps aux | grep $json | grep -v 'grep'| awk '{print $2}')
  $folder/plugin_$name $json
done


