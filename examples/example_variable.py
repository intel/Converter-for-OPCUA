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
sys.path.append("../pyutilities")
import logging
import time

from opcua import Client
from opcua import ua
from opcua import crypto
from security.config_security import UaSecurity

class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another 
    thread if you need to do such a thing
    """

    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val)
        print(data)

    def event_notification(self, event):
        print("Python: New event", event)

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)

    client = Client("opc.tcp://localhost:4840")
    uasecurity = UaSecurity();
    if uasecurity.get_securitytype() == 'tls':
        server_cert,client_cert,private_key = uasecurity.get_certificates()
        mode = uasecurity.get_securitymode()
        policy = uasecurity.get_securitypolicy()
        if server_cert == None:
            print('tls is enabled, but server cert is missing with current configuration')
            sys.exit(-1)
        if private_key == None:
            print('tls is enabled, but private key is missing with current configuration')
            sys.exit(-1)
        #client.load_client_certificate(server_cert)
        #client.load_private_key(private_key)
        client.set_security(
            getattr(crypto.security_policies, 'SecurityPolicy' + policy),
            server_cert,
            private_key,
            mode=getattr(ua.MessageSecurityMode, mode)
        )


    try:
        client.connect()

        # Client has a few methods to get proxy to UA nodes that should always be in address space such as Root or Objects
        root = client.get_root_node()
        print("Root node is: ", root)
        objects = client.get_objects_node()
        print("Objects node is: ", objects)

        # Node objects have methods to read and write node attributes as well as browse or populate address space
        print("Children of root are: ", root.get_children())
        data = root.get_child(["0:Objects", "2:MqttPlugin", "2:DeviceType#0", "2:Device#0", "2:Raw Data"])
        obj = root.get_child(["0:Objects", "2:MqttPlugin"])
        print("data is: ", data)

        # subscribing to a variable node
        handler = SubHandler()
        sub = client.create_subscription(500, handler)
        handle = sub.subscribe_data_change(data)
        while True:
            time.sleep(0.1)
    finally:
        client.disconnect()
