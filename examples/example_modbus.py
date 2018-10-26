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
import logging
import time

from opcua import Client
from opcua import ua

'''
1) Download and install pymodus
   # wget -c https://github.com/riptideio/pymodbus/archive/v1.4.0.tar.gz
   # tar zxvf v1.4.0.tar.gz
   # cd pymodbus-1.4.0
   # python3 setup.py install

2) Test steps:
	Terminal 1: Enter pymodbus-1.4.0 folder, to start the plugin service and TCP server simulator
	# python3 examples/common/synchronous_server.py

	Terminal 2: Enter opcua_plguin folder, to start the plugin service and TCP server simulator
	# python3 plugin-modbus.py plugin_modbus.json

	Terminal 3: Enter opcua_converter, to start opcua mapper server
	# python3 opcua_converter.py "modus"

	Terminal 4: Enter opcua_converter, to start opcua test client
	# python3 test_modus.py
'''

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    #logger = logging.getLogger("KeepAlive")
    # logger.setLevel(logging.DEBUG)

    client = Client("opc.tcp://localhost:4840")

    # #connect using a user

    try:
        client.connect()

        # Client has a few methods to get proxy to UA nodes that should always
        # be in address space such as Root or Objects
        root = client.get_root_node()
        print("Root node is: ", root)
        objects = client.get_objects_node()
        print("Objects node is: ", objects)

        # Node objects have methods to read and write node attributes as well
        # as browse or populate address space
        print("Children of root are: ", root.get_children())

        device1 = '127.0.0.1:5020'
        modbus_client = root.get_child(["0:Objects", "2:ModbusPlugin"])

        res = modbus_client.call_method("2:connect", device1)
        print("method result is: ", res)

        res = modbus_client.call_method("2:read_coils", device1, 1, 32)
        print("method result is: ", res)

        res = modbus_client.call_method("2:write_coil", device1, 1, True)
        print("method result is: ", res)

        res = modbus_client.call_method(
            "2:write_coils", device1, 1, [True] * 10)
        print("method result is: ", res)

        res = modbus_client.call_method(
            "2:read_discrete_inputs", device1, 1, 32)
        print("method result is: ", res)

        res = modbus_client.call_method(
            "2:read_holding_registers", device1, 1, 32)
        print("method result is: ", res)

        res = modbus_client.call_method("2:write_register", device1, 1, 18)
        print("method result is: ", res)

        res = modbus_client.call_method(
            "2:write_registers", device1, 1, [18] * 10)
        print("method result is: ", res)

        res = modbus_client.call_method(
            "2:read_input_registers", device1, 1, 32)
        print("method result is: ", res)

        res = modbus_client.call_method("2:disconnect", device1)
        print("method result is: ", res)

        print('\r\ndone')

    finally:
        client.disconnect()
