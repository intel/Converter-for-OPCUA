# !/usr/bin/env python3.5
# -*- coding: utf-8 -*-
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


import time
import signal
import argparse

from opcua import Client


class SubHandler(object):
    def datachange_notification(self, node, val, data):
        print(val)


class OpcuaSubClient():
    def __init__(self, sub_handler=SubHandler):
        self.server_uri = "opc.tcp://localhost:4840"
        self.client = Client(self.server_uri)
        self.is_connect = False
        self.sub = None
        self.root = None
        self.sub_handler = sub_handler()
        self.handle = None
        self.connect()

    def connect(self):
        try:
            self.client.connect()
            self.is_connect = True
            self.root = self.client.get_root_node()
            self.sub = self.client.create_subscription(1000, self.sub_handler)
        except Exception as e:
            self.is_connect = False
            raise e

    def dis_connect(self):
        if self.is_connect:
            self.client.disconnect()
            self.is_connect = False
            self.root = None
            self.sub = None

    def subscribe(self, qualified_list):
        val_node = self.root.get_child(qualified_list)
        if val_node:
            self.handle = self.sub.subscribe_data_change(val_node)

    def unsubscribe(self):
        if self.handle:
            self.sub.unsubscribe(self.handle)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--qualified_name', dest='qualified_name',
                        action='store', required=True, help='qualified name')
    args = parser.parse_args()

    qualified_list = args.qualified_name.split('/')
    qualified_list.insert(0, '0:Objects')

    is_stop = False

    opc = None
    try:
        opc = OpcuaSubClient()
    except BaseException:
        print('connect opcua server failed.')
        exit(1)

    if opc:
        try:
            opc.subscribe(qualified_list)
        except Exception as e:
            print(e)
            is_stop = True

    def shutdown(*args, **kwargs):
        nonlocal is_stop
        is_stop = True
        if opc:
            opc.unsubscribe()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    while not is_stop:
        time.sleep(1)

    opc.dis_connect()


if __name__ == '__main__':
    main()
