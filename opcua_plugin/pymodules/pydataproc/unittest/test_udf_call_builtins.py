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

import unittest

from opcua import Client
import time


class TestUAClient(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    # @unittest.skip
    def test_udf_call_builtins(self):
        client = Client("opc.tcp://localhost:4840")
        try:
            client.connect()
            root = client.get_root_node()
            objects = client.get_objects_node()
            obj = root.get_child(["0:Objects", "2:DataProcPlugin"])
            print("\nSet UDF to udf_call_builtins.py and wait for 10 secs")
            ret = obj.call_method("2:set_udf_file", "udf_call_builtins.py")
            self.assertEqual(ret, ['0', 'Success'])
            time.sleep(10)
        except BaseException:
            self.assertTrue(False)
        finally:
            client.disconnect()


if __name__ == "__main__":
    unittest.main()
