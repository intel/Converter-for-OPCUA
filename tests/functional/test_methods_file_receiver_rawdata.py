# -*- coding: UTF-8 -*-
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

import sys
import time

from opcua import Client
from opcua import ua


class SubHandler(object):
    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val)


if __name__ == "__main__":
    # set opcua server endpoint, fotmat as opc.tcp:<server ip>:<port>
    server_endpoint = "opc.tcp://localhost:4840"

    client = Client(server_endpoint)
    client.connect()

    # Client has a few methods to get proxy to UA nodes that should always be
    # in address space such as Root or Objects
    root = client.get_root_node()
    print("Root node is: ", root)
    objects = client.get_objects_node()
    print("Children of objects are: ", objects.get_children())
    children = objects.get_children()
    obj = None
    for child in children:
        if "FileReceiverFactory" in child.get_display_name().to_string():
            obj = child
    assert obj, "The FileReceiverFactory Plugin is offline."
    data = root.get_child(
        ["0:Objects", "2:FileReceiverFactory", "2:Device#0", "2:Raw Data"])

    # subscribing to a variable node
    handler = SubHandler()
    sub = client.create_subscription(500, handler)
    handle = sub.subscribe_data_change(data)
    while True:
        time.sleep(1)

    client.disconnect()
