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

import math as Math


def mod(x, y):
    return Math.fmod(x, y)


def pow(x, y):
    return Math.pow(x, y)


def radians(x):
    return Math.radians(x)


def degrees(x):
    return Math.degrees(x)


def fahrenheit(c):
    return float(c) * 9.0 / 5.0 + 32


def celsius(f):
    return float(f) - 32 * 5.0 / 9.0
