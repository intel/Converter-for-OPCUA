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


usage="$(basename "$0") [-h] [-c config_file] [-k] [-s] -- program to load Intel opcua converter

where:
    -h : show this help
    -c : specify the module config file
    -k : kill the opcua converter service
    -s : start the process by using supervisord
    "

supervised=$false

if [ $# -ge 1 ]; then
  if [ $1 != '-c' ] && [ $1 != '-h' ] && [ $1 != '-k' ] && [ $1 != '-s' ]; then
    echo "$usage"
    exit
  fi
fi

while getopts ':hskc:' option; do
  case "$option" in
    h) echo "$usage"
       exit
       ;;
    s) supervised=true
       ;;
    c) cfg_file=$OPTARG
       ;;
    k) echo "kill the converter service"
       kill $(ps aux | grep 'supervisord' | awk '{print $2}')
       kill $(ps aux | grep '[p]ython3 opcua_converter' | awk '{print $2}')
       exit 1
       ;;
   \?) printf "illegal option: -%s\n" "$OPTARG" >&2
       echo "$usage" >&2
       exit 1
       ;;
  esac
done

if [ ! $supervised ] ;then
  if [ -z ${cfg_file+x} ] ;then
    python3 opcua_converter.py
  else
    python3 opcua_converter.py -c $cfg_file
  fi
else
  def_conf=/etc/supervisor/supervisord.conf
  if [ ! -f $def_conf ]; then
    echo "No /etc/supervisor/supervisord.conf, Supervisord is not installed ??"
    exit 1
  fi
  cp $def_conf ./supervisord.conf
  kill $(ps aux | grep 'supervisord' | awk '{print $2}')
  sleep 1

  if [ -z ${cfg_file+x} ] ;then
    command="python3 opcua_converter.py"
  else
    command="python3 opcua_converter.py -c $cfg_file"
  fi

  echo "
      [program:opcua_converter]
          command = $command
          autostart = true
          startsecs = 5
          autorestart = true
          startretries = 3
          redirect_stderr = true
          stdout_logfile_maxbytes = 20MB
          stdout_logfile_backups = 20
          stdout_logfile = ./stdout.log" | sed 's/^[ \t]*//g' >> supervisord.conf
  supervisord -c ./supervisord.conf
fi
