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


if __name__ == "__main__":
    t = Unittest()

    print('test finish')
