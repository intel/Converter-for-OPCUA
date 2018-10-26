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

import os
import sys
import unittest

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, SCRIPT_DIR + '/../')
sys.path.insert(0, SCRIPT_DIR + '/../../../../pyutilities')
sys.path.insert(0, SCRIPT_DIR + '/../../')

from plugin_main import MqttPluginEntity
from plugin_main import MqttPluginConfig
from plugin_main import MqttPluginClient


class TestPluginMain(unittest.TestCase):
    def setUp(self):
        e = MqttPluginEntity(SCRIPT_DIR + '/../plugin_mqtt.json')
        c = MqttPluginConfig(SCRIPT_DIR + '/../default.conf')
        self.t = MqttPluginClient(e, c)
        self.t.start()

    def tearDown(self):
        self.t.stop()
        self.t = None

    def test_send_T1(self):
        name = 'Device#0'
        topic = 'req/MqttPlugin'
        msg = None
        res = self.t.send(name, topic, msg)
        self.assertEqual(res['data'], 'succeeded to send data')
        print("result:", res)

    def test_send_T2(self):
        name = 'Device#2'
        topic = 'req/MqttPlugin'
        msg = None
        res = self.t.send(name, topic, msg)
        self.assertEqual(res['data'], 'succeeded to send data')
        print("result:", res)

    def test_send_T3(self):
        name = 'Device#1'
        topic = 'req/MqttPlugin'
        msg = None
        res = self.t.send(name, topic, msg)
        self.assertEqual(res['data'], 'the host name was not connected')
        print("result:", res)

    def test_send_F(self):
        name = 'Device#10'
        topic = 'req/MqttPlugin'
        msg = None
        res = self.t.send(name, topic, msg)
        self.assertEqual(res['data'], 'the host name was not initiated')
        print("result:", res)


if __name__ == "__main__":
    unittest.main(verbosity=2)
