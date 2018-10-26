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
        '''self.t.connect("127.0.0.1:5020")'''

    def tearDown(self):
        self.t.stop()
        '''self.t.disconnect("127.0.0.1:5020")'''
        self.t = None

    def test_plugin_main_is_client_connected_T(self):
        res = self.t.is_client_connected("127.0.0.1:5020")
        self.assertTrue(res)
        print("result:", res)

    def test_plugin_main_is_client_connected_F(self):
        res = self.t.is_client_connected("")
        self.assertFalse(res)
        print("result:", res)


if __name__ == "__main__":
    unittest.main(verbosity=2)
