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

import importlib


def inject_module(to_, from_):
    setattr(to_, str(from_.__name__), importlib.import_module(from_.__name__))


class TestCheckUDF(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_injection(self):
        module_for_injection = importlib.import_module("module_for_injection")
        module_injected = importlib.import_module("module_injected")

        # not injected
        self.assertFalse(module_for_injection.call_injected())
        # inject module
        inject_module(module_for_injection, module_injected)
        # test injected
        self.assertTrue(module_for_injection.call_injected())

    def test_injection_builtins(self):
        module_for_injection = importlib.import_module("module_for_injection")
        module_injected = importlib.import_module("module_injected")
        # inject module
        inject_module(module_for_injection, module_injected)
        self.assertEqual(0.9, module_for_injection.call_injected_fabs(-0.9))


if __name__ == "__main__":
    unittest.main()
