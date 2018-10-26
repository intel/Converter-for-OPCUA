#!/bin/bash
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


git clone https://github.com/duangenquan/YoloV2NCS.git
cd YoloV2NCS
git checkout 6cfe9408763cda89beb8c7c532c67a222a3c09ad
make
cp detectionExample/libpydetector.so ../
cp detectionExample/ObjectWrapper.py ../

