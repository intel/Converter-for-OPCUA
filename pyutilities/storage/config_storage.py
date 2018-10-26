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

import sys
import os
import os.path

import logging
from logging.handlers import RotatingFileHandler
from configger.config_parser import ConfigLoader


class UaStorage(object):

    def __init__(self, credential=None):
        if credential is None:
            self.config = ConfigLoader()
        else:
            self.config = ConfigLoader(credential)
        self.configdict = self.config.ConfigSectionMap('Storage')

    def get_storagetype(self):
        if 'dataset' in self.configdict:
            return self.configdict['dataset']
        return 'memory'

    def get_sqliteconfig(self):
        if 'path' in self.configdict:
            return self.configdict['path']
        return 'default.db'

    def get_mongoconfig(self):
        host = 'localhost'
        port = 27017
        path = 'history'
        if 'host' in self.configdict:
            host = self.configdict['host']
        if 'port' in self.configdict:
            port = int(self.configdict['port'])
        if 'path' in self.configdict:
            path = self.configdict['path']
        return host, port, path
