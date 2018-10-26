# --coding:utf-8--
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

# -----------------------------
# Copyright by Intel
# -----------------------------

import os
import configparser
import copy

from logservice.logservice import LogService

logger = LogService.getLogger(__name__)


class BasePluginConfig(object):

    def __init__(self, config_fp=None):
        self.env_fp = config_fp
        self.env = {
            'Logging': None,
            'Security': None,
            'Amqp': None
        }
        if config_fp and (os.path.isfile(config_fp)):
            self.config = configparser.ConfigParser()
            self.config.read(config_fp, encoding='utf-8')
            self._parse()

    def _parse(self):
        if self.config.has_section('Logging'):
            self.env['Logging'] = {}
            log_type = self.config.get('Logging', 'type')
            if log_type not in ['file', 'all', 'none', 'console']:
                logger.error("config file Logging section has error")
                raise Exception(
                    '%s : Logging section type option incorrect',
                    os.path.basename(
                        self.env_fp))
            else:
                self.env['Logging']['output'] = log_type

            if log_type in ['file', 'all']:
                log_file = self.config.get('Logging', 'file')
                if not log_file:
                    logger.error("config file Logging section has error")
                    raise Exception(
                        '%s : Logging section file option incorrect',
                        os.path.basename(
                            self.env_fp))
                else:
                    self.env['Logging']['fp'] = log_file

            try:
                self.env['Logging']['level_str'] = self.config.get(
                    'Logging', 'level')
                self.env['Logging']['maxsize'] = self.config.getint(
                    'Logging', 'maxbytes')
            except BaseException:
                logger.exception("config file Logging section has error")

        if self.config.has_section('Security'):
            self.env['Security'] = {}
            try:
                self.env['Security']['tls'] = self.config.getboolean(
                    'Security', 'tls')
                if self.env['Security']['tls']:
                    self.env['Security']['cafile'] = self.config.get(
                        'Security', 'cafile')
                    self.env['Security']['cerfile'] = self.config.get(
                        'Security', 'cerfile')
                    self.env['Security']['keyfile'] = self.config.get(
                        'Security', 'keyfile')
            except configparser.NoOptionError as err:
                logger.exception("config file Security section has error")
                raise Exception(
                    '%s : Security section incorrect',
                    os.path.basename(
                        self.env_fp))

        if self.config.has_section('Amqp'):
            self.env['Amqp'] = {}
            try:
                self.env['Amqp']['url'] = self.config.get('Amqp', 'url')
            except configparser.NoOptionError as err:
                logger.exception("config file Amqp section has error")
                raise Exception(
                    '%s : Security section incorrect',
                    os.path.basename(
                        self.env_fp))

    def fetch_logger_env(self):
        return copy.deepcopy(self.env['Logging'])

    def fetch_security_env(self):
        return copy.deepcopy(self.env['Security'])

    def fetch_mq_env(self):
        return copy.deepcopy(self.env['Amqp'])
