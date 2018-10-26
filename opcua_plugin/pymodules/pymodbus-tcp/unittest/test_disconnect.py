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

    def tearDown(self):
        self.t = None

    def test_plugin_main_disconnect_T(self):
        self.t.connect("127.0.0.1:5020")
        res = self.t.disconnect("127.0.0.1:5020")
        self.assertEqual(res['data'], 'disconnect success')
        print("result:", res)

    def test_plugin_main_disconnect_F1(self):
        self.t.connect("127.0.0.1:5020")
        res = self.t.disconnect("0.0.0.1:5020")
        self.assertEqual(res['data'], 'device not found')
        print("result:", res)

    def test_plugin_main_disconnect_F2(self):
        self.t.start()
        res = self.t.disconnect("127.0.0.1:5020")
        self.assertEqual(res['data'], 'disconnect not allow')
        print("result:", res)
        self.t.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
