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


class UaLogger(object):

    def __init__(self, logger=logging.getLogger(__name__), credential=None):
        if credential is None:
            self.config = ConfigLoader()
        else:
            self.config = ConfigLoader(credential)
        self.configdict = self.config.ConfigSectionMap('Logging')
        self.configdict['console'] = 'False'
        self.logger = logger

    def get_loggerformat(self):
        if self.configdict['format'] == 'standard':
            return "%(asctime)s %(levelname)s %(filename)s:%(lineno)s - %(message)s"
        else:
            return "%(asctime)s %(levelname)s %(filename)s:%(lineno)s - %(message)s"

    def get_loggerlevel(self):
        if self.configdict['level'] == 'critical':
            return logging.CRITICAL
        elif self.configdict['level'] == 'error':
            return logging.ERROR
        elif self.configdict['level'] == 'warning':
            return logging.WARNING
        elif self.configdict['level'] == 'info':
            return logging.INFO
        elif self.configdict['level'] == 'debug':
            return logging.DEBUG
        else:
            return logging.NOTSET

    def set_loggerlevel(self, level):
        if level in ['critical', 'error', 'warning', 'info', 'debug']:
            self.configdict['level'] = level

    def set_loggerpath(self, path):
        self.configdict['path'] = path

    def enable_console(self):
        self.configdict['console'] = 'True'

    def enable_logger(self, logfile):
        path = self.configdict['path']
        if not os.path.isdir(path):
            os.makedirs(path)
        curdir = os.getcwd()
        os.chdir(path)
        logging.basicConfig(filename=logfile, level=self.get_loggerlevel())
        loghandler = RotatingFileHandler(
            logfile, maxBytes=int(
                self.configdict['maxbytes']), backupCount=int(
                self.configdict['file_count']))
        formatter = logging.Formatter(self.get_loggerformat())
        loghandler.setFormatter(formatter)
        # self.logger.setLevel(self.get_loggerlevel())
        self.logger.addHandler(loghandler)
        os.chdir(curdir)
        if self.configdict['console'] == 'True':
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
