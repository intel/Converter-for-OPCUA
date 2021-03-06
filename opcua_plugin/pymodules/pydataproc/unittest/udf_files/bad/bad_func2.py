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

import json


def process(row_data_json):
    json_obj = json.loads(row_data_json)
    passed = False
    result = None

    def foobar():
        pass

    if json_obj['line'] != 1:
        passed = False
        result = None
    else:
        passed = True
        result = json.dumps({
            'ts': json_obj['ts'],
            'measurement': json_obj['measurement']
        })

    return passed, result
