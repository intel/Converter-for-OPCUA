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

usage="$(basename "$0") [-h] [-c config_file] [-k [plugin_name]] -- program to load OPC-UA plugins

where:
    -h : show this help
    -c : specify the module config file(default ./modules.conf)
    -k : kill plugin(s), if no name specified, then it means to kill all the plugins
    "

cfg_file=./modules.conf

if [ $# -ge 1 ]; then
  if [ $1 != '-h' ] && [ $1 != '-c' ] && [ $1 != '-k' ]; then
    echo "$usage"
    exit
  fi
fi

while getopts ':hc:k:' option; do
  case "$option" in
    h) echo "$usage"
       exit
       ;;    
    c) cfg_file=$OPTARG
       ;;
    k) plugin_name=$OPTARG
       echo "$(basename "$0"): Kill plugin \"$plugin_name\""       
       kill -9 $(pgrep -f "pymodules/loader.py pymodules/pymqtt") > /dev/null 2>&1       
       exit
       ;;
    :) if [ $OPTARG = "k" ]; then
         echo "$(basename "$0"): Kill all plugins"
         kill -9 $(pgrep -f pymodules/loader.py) > /dev/null 2>&1
         kill -9 $(pgrep -f cmodules/loader.sh) > /dev/null 2>&1
       else
         printf "missing argument for -%s\n" "$OPTARG" >&2
         echo "$usage" >&2
       fi
       exit 1
       ;;
   \?) printf "illegal option: -%s\n" "$OPTARG" >&2
       echo "$usage" >&2
       exit 1
       ;;
  esac
done

PY_MODULES=` gawk '/^\s*python modules:/ {_cdr_par_=1}\
             /^\s*pymodules/{ if (_cdr_par_==1) {print $1} }\
         ' ${cfg_file}`

C_MODULES=` gawk '/^\s*c modules:/ {_cdr_par_=1}\
             /^\s*cmodules*/{ if (_cdr_par_==1) {print $1} }\
         ' ${cfg_file}`

kill -9 $(pgrep -f pymodules/loader.py) > /dev/null 2>&1
for element in $PY_MODULES
do
  module=${element#*/}
  echo "$(basename "$0"): Loading Python module \"${module}\""
  if [ -z ${module%py27*} ]; then      
      python2.7 pymodules/loader.py $element &
  else      
      python3 pymodules/loader.py $element &
  fi
done

kill -9 $(pgrep -f cmodules/loader.sh) > /dev/null 2>&1
for element in $C_MODULES
do
  echo "$(basename "$0"): Loading C module \"${element#*/}\""
  sh cmodules/loader.sh $element &
done
