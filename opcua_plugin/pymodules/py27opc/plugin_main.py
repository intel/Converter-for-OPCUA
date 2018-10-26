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
import sys
import os
import json
import threading
import time

opcua_path = os.path.split(os.path.realpath(__file__))[0] + "/../../"
sys.path.insert(0, opcua_path)
sys.path.append(opcua_path + "pymodules")
sys.path.append(opcua_path + "../pyutilities")
sys.path.append(opcua_path + "pymodules/py27opc/OpenOPC-1.3.1/src")

import OpenOPC

from client import BasePluginClient
from entity import BasePluginEntity
from config import BasePluginConfig
from ret_codes import ReturnCodes
from logservice.logservice import LogService

logger = LogService.getLogger(__name__)


class OpcPluginEntity(BasePluginEntity):
    def __init__(self, file_name):
        super(OpcPluginEntity, self).__init__(file_name)


class OpcPluginConfig(BasePluginConfig):
    def __init__(self, config_fp):
        super(OpcPluginConfig, self).__init__(config_fp)


class OpcPluginClient(BasePluginClient):
    def __init__(self, entity, config):
        super(OpcPluginClient, self).__init__(entity, config)
        self.plugin_node = self.entity.get_custom_nodes()[0]
        self.gateway = None
        self.opc_host = None
        self.opc_serv = None
        self.opc = None
        self.connected = False
        self.is_stop = True
        self._main = None

    def _start(self):
        logger.debug('opc plugin connecting starting......')
        self.gateway = self.entity.get_property(
            self.plugin_node, 'server address').value
        self.opc_host = self.gateway
        self.opc_serv = self.entity.get_property(
            self.plugin_node, 'server name').value
        try:
            self.opc = OpenOPC.open_client(self.gateway)
            self.opc.connect(self.opc_serv, self.opc_host)
            self.connected = True
            logger.info('opc plugin connect server success')
        except BaseException:
            logger.exception('connect opc server failed, %s' % self.gateway)
            self.opc = None
            self.connected = False

        if self.connected:
            self._main = threading.Thread(
                target=self._plugin_main, args=(None,))
            self._main.setDaemon(True)
            self.is_stop = False
            self._main.start()

    def _stop(self):
        if not self.is_stop:
            self.is_stop = True

        if self._main:
            self._main.join()

        if self.opc:
            try:
                self.opc.close()
            except BaseException:
                logger.exception('opc disconnect except')
            finally:
                self.opc = None
                self.connected = False
            logger.info('opc plugin disconnect the opc server')

    def start(self):
        self._start()
        super(OpcPluginClient, self).start()

    def stop(self):
        self._stop()
        super(OpcPluginClient, self).stop()

    def restart(self, *args, **kwargs):
        self._stop()
        self._start()

    def is_client_connected(self, *args, **kwargs):
        return self.connected

    def get_client_state(self, *args, **kwargs):
        return {
            'name': self.gateway,
            'connected': self.connected,
            'opc_host': self.opc_host,
            'opc_serv': self.opc_serv,
        }

    def getstate(self, *args, **kwargs):
        return {
            'code': ReturnCodes.Good,
            'data': self.get_client_state()
        }

    def read(self, tag):
        ret_code = 0
        result = 'server disconnected'
        if self.connected:
            val, quality, ts = self.opc.read(tag)
            if quality == 'Good':
                ret_code = ReturnCodes.Good

            result = json.dumps({
                'val': val,
                'quality': quality,
                'ts': ts,
            })

        return {'code': ret_code, 'data': result}

    def write(self, tag, val):
        ret_code = 0
        info = 'server disconnected'
        if self.connected:
            status, info = self.opc.write((tag, val), include_error=True)
            if status == 'Success':
                ret_code = ReturnCodes.Good

        return {'code': ret_code, 'data': info}

    def notify_data(self, data, node):
        if data is not None:
            pair_variable = node.get_pair_friend()
            parent = node.get_parent()
            self.pub_data(parent.name, pair_variable.name, data)

    def _plugin_main(self, *args, **kwargs):
        now = 0

        # delay 1 second a void race condition
        time.sleep(1)
        while not self.is_stop:
            period_node = self.entity.get_property(self.plugin_node, 'period')
            if period_node is None:
                continue
            now += 1
            if now % int(period_node.value) == 0:
                tag = self.entity.get_property(self.plugin_node, 'tag')
                data = self.read(tag.value)
                self.notify_data(json.dumps(data), tag)
            time.sleep(1)


def plugin_main(*args, **kwargs):
    plugin_entity = OpcPluginEntity(args[0])
    plugin_config = OpcPluginConfig(args[1])
    plugin_client = OpcPluginClient(plugin_entity, plugin_config)
    plugin_client.start()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python27 plugin_main.py <plugin file>')
    else:
        plugin_path = os.path.split(os.path.realpath(__file__))[0]
        sys.path.append(plugin_path)
        entity_file = sys.argv[1]

        config_fp = None
        for (root, dirs, files) in os.walk(os.path.abspath(plugin_path)):
            for f in files:
                if os.path.splitext(f)[1] == '.conf':
                    config_fp = os.path.join(root, f)
                    break

        plugin_main(entity_file, config_fp)
