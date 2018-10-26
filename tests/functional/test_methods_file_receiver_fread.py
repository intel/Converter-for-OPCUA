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


from base64 import b64decode, b64encode
from opcua import Client, ua

if __name__ == "__main__":
    # set opcua server endpoint, fotmat as opc.tcp:<server ip>:<port>
    server_endpoint = "opc.tcp://localhost:4840"
    if len(sys.argv) < 2:
        print('Usage: python test_method_fread.py <image_id>')
        sys.exit(-1)

    file_name = sys.argv[1] + '.bmp'
    client = Client(server_endpoint, 60)
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

    print('\r\ntest fread api - read', file_name)
    # file_name = 'c2ccd4a0-4788-11e8-8290-00163e0cb3ab.bmp'
    dev = root.get_child(["0:Objects", "2:FileReceiverFactory", "2:Device#0"])
    res = dev.call_method("2:fread", file_name)
    print('method result code is: ', res[0])
    if int(res[0]) is 0:
        file_bytes = b64decode(res[1])
        file = open(file_name, 'wb')
        file.write(file_bytes)
        file.close()
        print('file saved', file_name)

    print('\r\ndone')
    client.disconnect()
