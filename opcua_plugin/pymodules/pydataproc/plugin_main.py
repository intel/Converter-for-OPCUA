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
import sys
import importlib
from urllib.parse import urlparse

from client import BasePluginClient
from entity import BasePluginEntity
from config import BasePluginConfig
from logservice.logservice import LogService
from ret_codes import ReturnCodes

from amqp_client import AmqpClient
import check_udf
import tools

logger = LogService.getLogger(__name__)


class PluginEntity(BasePluginEntity):
    def __init__(self, file_name):
        super(PluginEntity, self).__init__(file_name)


class PluginConfig(BasePluginConfig):
    def __init__(self, config_fp):
        super(PluginConfig, self).__init__(config_fp)


class PluginClient(BasePluginClient):
    def __init__(self, entity, config):
        super(PluginClient, self).__init__(entity, config)
        self.plugin_folder_path = os.path.dirname(
            os.path.realpath(self.entity.file_name))
        self.udf_folder_path = self.plugin_folder_path + '/udf'
        # make udf folder if not exist
        if not os.path.exists(self.udf_folder_path):
            os.makedirs(self.udf_folder_path)

        self.source_topic = self.entity.get_property(
            self.entity.root_node, 'source_topic').value
        self.sink_topic = self.entity.get_property(
            self.entity.root_node, 'sink_topic').value
        self.udf_file = self.entity.get_property(
            self.entity.root_node, 'udf_file').value
        enabled = self.entity.get_property(
            self.entity.root_node, 'udf_enabled').value
        self.udf_enabled = enabled.lower() in ['yes', 'true', '1']

        # get amqp config
        amqp_url = config.fetch_mq_env()['url']
        url_parsed = urlparse(amqp_url)
        self.amqp_host = url_parsed.hostname
        self.amqp_user = url_parsed.username
        self.amqp_password = url_parsed.password

    def _start_processing(self):
        if (self.udf_enabled):
            self._set_udf_file(self.udf_file)
            if self._check_udf_file():
                logger.debug("Checking UDF succeed, start processing...")
                sys.path.insert(0, self.udf_folder_path)
                udf = importlib.import_module(
                    os.path.splitext(self.udf_file)[0])
                # inject built-in modules
                self._inject_builtins(udf)
                self.client = AmqpClient(
                    self.source_topic, self.sink_topic,
                    self.amqp_host, self.amqp_user, self.amqp_password)
                self.client.set_process_func(udf.process)
                self.client.run()
            else:
                logger.warn("Checking UDF failed, exiting...")
        else:
            logger.warn("UDF not enabled")

    def _stop_processing(self):
        if self.client:
            self.client.stop()

    def _restart_processing(self):
        self._stop_processing()
        self._start_processing()

    def _inject_builtins(self, udf_module):
        tools.inject_module(
            udf_module,
            importlib.import_module('udf_builtins'),
            name='udf')

    def _check_udf_file(self):
        if not check_udf.check_existance(self.udf_file_path):
            logger.warn("UDF file not exist")
            return False
        return check_udf.validate_udf_file(self.udf_file_path)

    def _set_udf_file(self, filename):
        self.udf_file = filename
        self.udf_file_path = self.udf_folder_path + '/' + self.udf_file

    def start(self):
        self._start_processing()

        # run BasePluginClient's start()
        super(PluginClient, self).start()

    def stop(self):
        self._stop_processing()

        # run BasePluginClient's stop()
        super(PluginClient, self).stop()

    def set_udf_enabled(self, is_enabled):
        enabled = is_enabled.lower() in ['yes', 'true', '1']
        if enabled:
            if not self.udf_enabled:
                self.udf_enabled = True
                self._start_processing()
        else:
            if self.udf_enabled:
                self.udf_enabled = False
                self._stop_processing()

        return {'code': ReturnCodes.Good, 'data': 'Success'}

    def set_udf_file(self, filename):
        if filename != self.udf_file:
            self._set_udf_file(filename)
            self._restart_processing()
        return {'code': ReturnCodes.Good, 'data': "Success"}

    def plugin_call(self, method, msg):
        json_out = super(PluginClient, self).plugin_call(method, msg)
        if json_out is None:
            func = getattr(self, method)
            json_out = func(msg)
        return json_out


def plugin_main(*args, **kwargs):
    plugin_entity = PluginEntity(args[0])
    plugin_config = PluginConfig(args[1])
    plugin_client = PluginClient(plugin_entity, plugin_config)
    plugin_client.start()
