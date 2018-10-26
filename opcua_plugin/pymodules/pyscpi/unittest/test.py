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

    def test_open(self, *args):
        obj = {
            'method': 'open',
            'data': args

        }
        print(self.mq_serv.request('ScpiPlugin', obj))

    def test_close(self, *args):
        obj = {
            'method': 'close',
            'data': args

        }
        print(self.mq_serv.request('ScpiPlugin', obj))

    def test_state(self, *args):
        obj = {
            'method': 'state',
            'data': args

        }
        print(self.mq_serv.request('ScpiPlugin', obj))

    def test_send(self, *args):
        obj = {
            'method': 'send',
            'data': args

        }
        print(self.mq_serv.request('ScpiPlugin', obj))


if __name__ == "__main__":
    t = Unittest()

    link = ''
    setting = ''
    status = ''
    data = ''

    t.test_open(link, setting)
    t.test_state(link, status)
    t.test_send(link, data)
    t.test_close(link)

    print('test finish')
