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
import paho.mqtt.client as mqtt
import ssl
import argparse

import time
import logging
import random

def process_mqtt(mqtt_client):
    # generate temperature and room Num
    t = time.time()
    t = round(t * 1000) / 1000
    room = random.randint(0, 10)
    temperature = random.randint(22,30)
    data = "{\"room\":" + str(room) + ",\"time\":" + str(t) + ",\"temperature\":" + str(temperature) + ",\""+"temperature exception"+"\"}"
    for top in tops:
        if top.strip():
            client.publish(top.strip(), data)
    time.sleep(interval / 1000)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)

    if len(sys.argv) < 3:
        print('Usage: python xxxx.py <time_interval(ms)> <topics>')
        sys.exit(-1)
    interval = int(sys.argv[1])
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
    parser.add_argument('--cacert',
                        dest='cacert',
                        action='store',
                        default=None,
                        help='mqtt password for auth.')
    (options, args) = parser.parse_known_args()
    auth = {}
#    if options.username:
#        auth['username'] = options.username
#    if options.password:
#        auth['password'] = options.password
    port = 1883
    if options.cacert == 'tls':
        port = 8883
        client = mqtt.Client("localhost", 8883)
        client.tls_set(
            ca_certs='ca.crt',
            certfile='client.crt',
            keyfile='client.key',
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1,
            ciphers=None)
    else:
        client = mqtt.Client("localhost", 1883)

    if options.username:
        client.username_pw_set(
            username=options.username,
            password=options.password)

    try:
        client.connect("localhost", port, 60)
    except BaseException:
        logger.info('mqtt plugin connected the broker fail')
    client.loop_start()

    if len(auth) is 1:
        print('mqtt is missing username or password')
        sys.exit(-1)
    loop = 0
    topic = sys.argv[2]
    tops = topic.split(',')
    while True:
        try:
            process_mqtt(client)
        except KeyboardInterrupt:
            break
