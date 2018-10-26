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


class UaSecurity(object):

    def __init__(self, credential=None):
        if credential is None:
            self.config = ConfigLoader()
        else:
            self.config = ConfigLoader(credential)
        self.configdict = self.config.ConfigSectionMap('Security')

    def get_securitytype(self):
        if 'tls' in self.configdict:
            if self.configdict['tls'] == 'true':
                return 'tls'
        return 'open'

    def get_securitymode(self):
        mode = None
        if 'mode' in self.configdict:
            mode = self.configdict['mode']
        return mode

    def get_securitypolicy(self):
        policy = None
        if 'policy' in self.configdict:
            policy = self.configdict['policy']
        return policy

    def get_certificates(self):
        server_cert = None
        client_cert = None
        private_key = None
        if 'server_cert' in self.configdict:
            server_cert = self.configdict['server_cert']
        if 'client_cert' in self.configdict:
            client_cert = self.configdict['client_cert']
        if 'private_key' in self.configdict:
            private_key = self.configdict['private_key']
        return server_cert, client_cert, private_key


class UaAmqpSecurity(object):

    def __init__(self, credential=None):
        if credential is None:
            self.config = ConfigLoader()
        else:
            self.config = ConfigLoader(credential)
        self.section = self.config.fetchSection('Amqp')

    def get_tls_confg(self):
        tls_config = None
        if self.section.getboolean('tls'):
            tls_config = {
                'tls': True,
                'cafile': self.section.get('cafile'),
                'cerfile': self.section.get('cerfile'),
                'keyfile': self.section.get('keyfile'),
            }
        return tls_config
