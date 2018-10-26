# -*- coding: utf-8 -*-
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
import configparser


class ConfigLoader(object):

    def __init__(self, credential='default.conf'):
        if credential == 'default.conf':
            self._config_file = os.path.dirname(
                os.path.realpath(__file__)) + '/' + credential
        else:
            self._config_file = credential
        if not os.path.exists(self._config_file):
            print('error: credential file is not found - ' + credential)
            return
        self.cfgparser = configparser.ConfigParser()
        self.cfgparser.read(self._config_file)

    def fetchSection(self, section):
        if self.cfgparser.has_section(section):
            return self.cfgparser[section]
        return None

    def ConfigSectionMap(self, section):
        config_dict = {}
        options = self.cfgparser.options(section)
        for option in options:
            try:
                config_dict[option] = self.cfgparser.get(section, option)
                if config_dict[option] == -1:
                    print("ConfigLoader: skip %s" % option)
            except BaseException:
                print("exception on %s!" % option)
                config_dict[option] = None
        return config_dict
