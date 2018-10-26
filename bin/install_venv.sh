#!/bin/bash

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

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUTPUT_PREFIX="[$(basename $0)]:"
VENV_NAME="venv"

cd $SCRIPT_DIR/..

if [ -d "venv" ]; then
    echo $OUTPUT_PREFIX virtualenv directory $VENV_NAME exists, remove the directory if you want to setup again!
    exit
fi

if ! [ -x "$(command -v virtualenv)" ]; then
    pip3 install virtualenv
else
    echo $OUTPUT_PREFIX virtualenv already installed!
fi

virtualenv $VENV_NAME
echo $OUTPUT_PREFIX virtualenv is setup, use 'source venv/bin/activate' to activatue!

cd $SCRIPT_DIR