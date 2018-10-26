# --coding:utf-8--
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

# -----------------------------
# Copyright by Intel
# -----------------------------

import sys
import paho.mqtt.publish as publish
import argparse
import shutil
import uuid

import time
import logging
import os
import random

index = 0
image_path = "image/"
folder_path = "../../pyfilesys/images/"


def process_mqtt():
    global index
    try:
        t = time.time()
        t = round(t * 1000) / 1000
        index += 1

        filename = file()

        dictstr = "{\"idx\":" + str(index) + ",\"time\":" + str(t) + ",\"samples\":" + str(1) + ",\"machine_id\":" + str(22) + ",\"part_id\":\"" + filename + \
            "\",\"image_id\":\"" + filename + "\",\"defects\":[{\"type\":\"Wrong type A\",\"count\":3}" + ",{\"type\":\"Wrong type B\",\"count\":5}" + "]}"
        publish.single(
            "proj_1/gw_1/raw0",
            dictstr,
            hostname="localhost",
            port=1883,
            auth=auth,
            qos=1)

        print(dictstr)

        time.sleep(interval / 1000)
    except ImportError as e:
        print(e)


def file():
    file_w = str(uuid.uuid1())
    try:
        file_r = str(random.randint(1, 3))
        image_check(folder_path)
        shutil.copyfile(
            image_path + file_r + ".bmp",
            folder_path + file_w + ".bmp")

    except ImportError as e:
        print(e)

    return file_w


def image_check(path):
    iterms = os.listdir(path)
    iterms = sorted(iterms, key=lambda x: filetime(x), reverse=False)
    print('------' + str(len(iterms)))
    if len(iterms) >= 100:
        i = 0
        while (i <= len(iterms) - 100):
            os.remove(path + iterms[i])
            i = i + 1


def filetime(file):
    stat_file = os.stat(folder_path + file)
    last_access_time = stat_file.st_atime
    return last_access_time


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)

    if len(sys.argv) < 2:
        print('Usage: python xxxx.py <time_interval(ms)>')
        sys.exit(-1)
    parser = argparse.ArgumentParser(
        description='Process mqtt sender argument')
    parser.add_argument('--user',
                        dest='username',
                        action='store',
                        default=None,
                        help='mqtt username for auth.')
    parser.add_argument('--password',
                        dest='password',
                        action='store',
                        default=None,
                        help='mqtt password for auth.')
    (options, args) = parser.parse_known_args()
    auth = {}
    if options.username:
        auth['username'] = options.username
    if options.password:
        auth['password'] = options.password
    if len(auth) is 1:
        print('mqtt is missing username or password')
        sys.exit(-1)
    index = 0
    interval = int(sys.argv[1])
    while True:
        try:
            process_mqtt()
        except KeyboardInterrupt:
            break
