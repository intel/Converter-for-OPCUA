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
import time

from mqservice import MsgQueueService


def test_install():
    sys.path.insert(0, '../OpenOPC-1.3.1/src')

    import OpenOPC

    gateway = '172.0.0.1'
    opchost = '172.0.0.2'
    opcserv = 'Matrikon.OPC.Simulation.1'
    taglist = ['Random.Int1', 'Random.String']


    opc = OpenOPC.open_client(gateway)
    opc.connect(opcserv, opchost)
    v = opc.read(taglist)
    opc.close()

    for i in range(len(v)):
        print(v[i])


class Unittest(object):

    def __init__(self):
        self.mq_serv = MsgQueueService('test_opc_queue')
        self.mq_serv.set_callback(self._recv)
        self.mq_serv.start(daemon=True)

    def _recv(self, json_in):
        print('AmqpOpcTest   _recv')
        print(json_in)

    def test_read(self, tag):
        obj = {
            'method': 'read',
            'data': [tag]

        }
        print(self.mq_serv.request('OpcPlugin', obj))

    def test_write(self, tag, val):
        obj = {
            'method': 'write',
            'data': [tag, val]

        }
        print(self.mq_serv.request('OpcPlugin', obj))

if __name__ == "__main__":
    t = Unittest()

    t.test_read('Random.String')
    t.test_read('Random.Int1')

    t.test_write('Triangle Waves.Real4', 100)
    t.test_write('Random.String', 100)
    t.test_write('Triangle Waves.Real8', '100')
    t.test_write('Triangle Waves.Real8', '1www00')

    print('test finish')
