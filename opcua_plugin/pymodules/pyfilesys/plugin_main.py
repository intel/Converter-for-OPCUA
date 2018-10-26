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
from base64 import b64decode, b64encode
from client import BasePluginClient
from entity import BasePluginEntity
from config import BasePluginConfig
from logservice.logservice import LogService
from ret_codes import ReturnCodes
import json

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
        self.folder_name = self.entity.get_property(
            self.entity.root_node, 'folder').value
        self.folder_path = os.path.split(os.path.realpath(self.entity.file_name))[
            0] + '/' + self.folder_name
        try:
            os.stat(self.folder_path)
        except BaseException:
            os.mkdir(self.folder_path)

    def fread(self, filename):
        file_path = self.folder_path + '/' + filename
        print(file_path)
        try:
            file_handle = open(file_path, 'rb')
            file_data = file_handle.read()
            file_handle.close()
        except Exception as e:
            logger.exception("fread error: %s", e.strerror)
            return {'code': ReturnCodes.PLUGIN_ParamError, 'data': e.strerror}

        if isinstance(file_data, bytes):
            base64_bytes = b64encode(file_data)
            base64_string = base64_bytes.decode('utf-8')
            json_out = {'code': ReturnCodes.Good, 'data': base64_string}
        else:
            return {
                'code': ReturnCodes.PLUGIN_ParamError,
                'data': 'File data corruption'}

        return json_out

    def fwrite(self, filename, bytes):
        file_bytes = b64decode(bytes)
        file_path = self.folder_path + '/' + filename
        try:
            file = open(file_path, 'wb')
            file.write(file_bytes)
            file.close()
            json_out = {'code': ReturnCodes.Good, 'data': "Success"}
        except Exception as e:
            logger.exception("fread error: %s", e.strerror)
            return {'code': ReturnCodes.PLUGIN_ParamError, 'data': e.strerror}

        return json_out

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
