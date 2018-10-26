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
        self.mq_serv = MsgQueueService('test_queue')
        self.mq_serv.set_callback(self._recv)
        self.mq_serv.start(daemon=True)

    def _recv(self, json_in):
        print('Unittest   _recv')
        print(json_in)

    def test_put(self, key, value):
        obj = {
            'method': 'put',
            'data': [key, value]

        }
        print(self.mq_serv.request('KvPlugin', obj))

    def test_get(self, key):
        obj = {
            'method': 'get',
            'data': [key]

        }
        print(self.mq_serv.request('KvPlugin', obj))

    def test_delete(self, key):
        obj = {
            'method': 'delete',
            'data': [key]

        }
        print(self.mq_serv.request('KvPlugin', obj))

    def test_getstate(self, name=None):
        obj = {
            'method': 'getstate',
            'data': [name]

        }
        print(self.mq_serv.request('KvPlugin', obj))


if __name__ == "__main__":
    t = Unittest()

    t.test_put('laozh_key1', '123')
    t.test_get('laozh_key1')
    t.test_delete('laozh_key1')
    t.test_get('laozh_key1')

    t.test_getstate()

    print('test finish')
