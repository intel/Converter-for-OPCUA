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
sys.path.insert(0, '../../../../pyutilities')

from mqservice import MsgQueueService


class Unittest(object):
    def __init__(self):

        self.queue = 'ModbusPlugin-TCP'

        self.mq_serv = MsgQueueService('test_queue')
        self.mq_serv.set_callback(self._recv)
        self.mq_serv.start(daemon=True)

    def _recv(self, json_in):
        print('Unittest   _recv')
        print(json_in)

    def test_write_coil(self, uri, address, value):
        obj = {
            'method': 'write_coil',
            'data': [uri, address, value]

        }
        print(self.mq_serv.request(self.queue, obj))

    def test_write_register(self, uri, address, value):
        obj = {
            'method': 'write_register',
            'data': [uri, address, value]

        }
        print(self.mq_serv.request(self.queue, obj))

    def test_read_coils(self, uri, address, count):
        obj = {
            'method': 'read_coils',
            'data': [uri, address, count]

        }
        print(self.mq_serv.request(self.queue, obj))

    def test_read_discrete_inputs(self, uri, address, count):
        obj = {
            'method': 'read_discrete_inputs',
            'data': [uri, address, count]

        }
        print(self.mq_serv.request(self.queue, obj))

    def test_read_holding_registers(self, uri, address, count):
        obj = {
            'method': 'read_holding_registers',
            'data': [uri, address, count]

        }
        print(self.mq_serv.request(self.queue, obj))

    def test_read_input_registers(self, uri, address, count):
        obj = {
            'method': 'read_input_registers',
            'data': [uri, address, count]

        }
        print(self.mq_serv.request(self.queue, obj))


if __name__ == "__main__":
    t = Unittest()
    uri = '127.0.0.1:5020'

    t.test_write_coil(uri, '5', '0')
    t.test_write_register(uri, '15', 9)

    t.test_read_coils(uri, '5', 10)
    t.test_read_discrete_inputs(uri, "10", "10")
    t.test_read_holding_registers(uri, "100", "112")
    t.test_read_input_registers(uri, "100", "10")

    print('test finish')
