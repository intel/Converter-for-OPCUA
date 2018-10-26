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

from plugin_main import ModbusPluginClient
from plugin_main import ModbusPluginEntity
from plugin_main import ModbusPluginConfig


class TestPluginMain(unittest.TestCase):
    def setUp(self):
        e = ModbusPluginEntity(SCRIPT_DIR + '/../plugin_modbus.json')
        c = ModbusPluginConfig(SCRIPT_DIR + '/../default.conf')
        self.t = ModbusPluginClient(e, c)
        self.t.start()

    def tearDown(self):
        self.t.disconnect("127.0.0.1:5020")
        self.t.stop()
        self.t = None

    def test_plugin_main_connect_T(self):
        res = self.t.connect("127.0.0.1:5020")
        self.assertEqual(res['data'], 'connect success')
        print("result:", res)

    def test_plugin_main_connect_F1(self):
        res = self.t.connect("0.0.0.1:5020")
        self.assertEqual(res['data'], 'connect failed')
        print("result:", res)

    def test_plugin_main_connect_F2(self):
        res = self.t.connect("127.0.0.1")
        self.assertEqual(
            res['data'],
            'modbus-tcp plugin connect parameter error')
        print("result:", res)


if __name__ == "__main__":
    unittest.main(verbosity=2)
