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

usage="$(basename "$0") [-h] [-c config_file] [-k [plugin_name]] [-s] -- program to load Intel opcua plugins

where:
    -h : show this help
    -c : specify the module config file(default ./modules.conf)
    -k : kill plugin(s), if no name specified, then it means to kill all the plugins
    -s : start the process by using supervisord
    "

cfg_file=./modules.conf
supervised=$false

if [ $# -ge 1 ]; then
  if [ $1 != '-c' ] && [ $1 != '-h' ] && [ $1 != '-k' ] && [ $1 != '-s' ]; then
    echo "$usage"
    exit
  fi
fi

while getopts ':hsc:k:' option; do
  case "$option" in
    h) echo "$usage"
       exit
       ;;
    s) supervised=true
       ;;
    c) cfg_file=$OPTARG
       ;;
    k) plugin_name=$OPTARG
       echo "kill plugin" $plugin_name
       kill $(ps aux | grep 'pymodules/loader.py pymodules/$plugin_name' | awk '{print $2}')
       kill $(ps aux | grep $plugin_name | grep -v 'grep' | awk '{print $2}')
       exit
       ;;
    :) if [ $OPTARG = "k" ]; then
         echo "kill all plugins"
         kill $(ps aux | grep 'supervisord' | awk '{print $2}')
         kill $(ps aux | grep 'pymodules/loader.py' | awk '{print $2}')
         kill $(ps aux | grep -E 'plugin_c|loader.sh' | grep -v 'grep' | awk '{print $2}')
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

PY_MODULES=` gawk '$0~/^[\011 ]*python modules*:*/ {_cdr_par_=1}\
             $0~/^[\011 ]\s*pymodules*/{ if(_cdr_par_==1){print substr($1, 1, length($1)-1)}}\
         ' ${cfg_file}`

C_MODULES=` gawk '$0~/^[\011 ]*c modules*:*/ {_cdr_par_=1}\
             $0~/^[\011 ]\s*cmodules*/{ if(_cdr_par_==1){print substr($1, 1, length($1)-1)}}\
         ' ${cfg_file}`

if [ ! $supervised ]
then
  for element in $PY_MODULES
  do
    module=${element#*/}
    echo "loading Python module:" ${module}
    if [ -z ${module%py27*} ]; then
        kill $(ps aux | grep '[p]ython2.7 pymodules/loader.py '$element | awk '{print $2}')
        python2.7 pymodules/loader.py $element &
    else
        kill $(ps aux | grep '[p]ython3 pymodules/loader.py '$element | awk '{print $2}')
        python3 pymodules/loader.py $element &
    fi
  done

  for element in $C_MODULES
  do
    echo "loading C module:" ${element#*/}
    kill $(ps aux | grep $element | grep -v 'grep' | awk '{print $2}')
    cmodules/loader.sh $element &
  done
else
  def_conf=/etc/supervisor/supervisord.conf
  if [ ! -f $def_conf ]; then
    echo "No /etc/supervisor/supervisord.conf, Supervisord is not installed ??"
    exit 1
  fi
  cp $def_conf ./supervisord.conf
  kill $(ps aux | grep 'supervisord' | awk '{print $2}')
  sleep 1

  for element in $PY_MODULES
  do
    module=${element#*/}
    echo "loading Python module:" ${module}
    if [ -z ${module%py27*} ]; then
        cmd="python2.7"
    else
        cmd="python3"
    fi
    echo "
        [program:${element#*/}]
            command = $cmd pymodules/loader.py $element
            autostart = true
            startsecs = 5
            autorestart = true
            startretries = 3
            redirect_stderr = true
            stdout_logfile_maxbytes = 20MB
            stdout_logfile_backups = 20
            stdout_logfile = $element/stdout.log" | sed 's/^[ \t]*//g' >> supervisord.conf
  done

  for element in $C_MODULES
  do
    echo "loading C module:" ${element#*/}
    echo "
        [program:${element#*/}]
            command = cmodules/loader.sh $element
            autostart = true
            startsecs = 5
            autorestart = true
            startretries = 3
            redirect_stderr = true
            stdout_logfile_maxbytes = 20MB
            stdout_logfile_backups = 20
            stdout_logfile = $element/stdout.log" | sed 's/^[ \t]*//g' >> supervisord.conf
  done

  supervisord -c ./supervisord.conf
fi
