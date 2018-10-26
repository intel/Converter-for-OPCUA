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


import os
import sys
import configparser

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))))


class Options(object):
    def __init__(self, config_name='default.conf'):
        self.config_fp = os.path.join(
            os.path.dirname(
                os.path.realpath(__file__)),
            config_name)
        self.config = configparser.ConfigParser()
        self.config.read(self.config_fp)

        self.plugin_folder = self.get_plugin_folder()
        self.plugin_options = {}
        self.parse_plugins()

    def get_env_dir(self):
        return os.path.join(BASE_DIR, 'opcua_plugin')

    def get_pyplugin_dir(self):
        return os.path.join(BASE_DIR, 'opcua_plugin', 'pymodules')

    def get_loader_py(self):
        os.path.join(self.plugin_folder, 'loader.py')

    def get_plugin_folder(self):
        return os.path.join(BASE_DIR, 'opcua_plugin', 'pymodules')

    def parse_plugins(self):
        enabled_list = self.config.get('Plugin', 'enabled').split(',')
        for name in enabled_list:
            section_name = name + '_plugin'
            plugin_name = self.config.get(section_name, 'name')
            auto_start = self.config.getboolean(section_name, 'auto_start')
            auto_restart = self.config.getboolean(section_name, 'auto_restart')
            id = self.config.get(section_name, 'id')
            folder = self.config.get(section_name, 'folder')
            command = self.config.get(section_name, 'command')

            plugin_config = {
                'command': command,
                'plugin_name': plugin_name,
                'plugin_id': id,
                'folder': folder,
                'auto_start': auto_start,
                'auto_restart': auto_restart,
            }

            self.plugin_options[plugin_name] = plugin_config

        self.plugin_options['manager'] = {
            'command': None,
            'plugin_name': 'manager',
            'plugin_id': 'manager',
            'folder': 'manager',
            'auto_start': True,
            'auto_restart': True,
            'manager': True,
        }
