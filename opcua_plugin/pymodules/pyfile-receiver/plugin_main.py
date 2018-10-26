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
from client import BasePluginClient
from entity import BasePluginEntity
from config import BasePluginConfig

import os
import time
import json
import paho.mqtt.client as mqtt
from base64 import b64decode, b64encode
from ret_codes import ReturnCodes
from logservice.logservice import LogService

logger = LogService.getLogger(__name__)


class FileReceiverPluginEntity(BasePluginEntity):
    def __init__(self, file_name):
        super(FileReceiverPluginEntity, self).__init__(file_name)

    def get_logger():
        return super(FileReceiverPluginEntity, self).get_logger()


class FileReceiverPluginConfig(BasePluginConfig):
    def __init__(self, config_fp):
        super(FileReceiverPluginConfig, self).__init__(config_fp)


class FileReceiverPluginClient(BasePluginClient):
    def __init__(self, entity, config):
        super(FileReceiverPluginClient, self).__init__(entity, config)
        self.mqtt_devices = self.entity.get_custom_nodes()
        self.mqtt_clients = {}
        self.folder_name = self.entity.get_property(
            self.mqtt_devices[0], 'Image Folder').value
        self.folder_path = os.path.split(os.path.realpath(self.entity.file_name))[
            0] + '/' + self.folder_name
        try:
            os.stat(self.folder_path)
        except BaseException:
            os.mkdir(self.folder_path)

        self.is_stop = False

    def _start(self):
        for device in self.mqtt_devices:
            mqttbroker = self.entity.get_property(device, 'Mqtt Broker')
            if mqttbroker is None:
                continue
            broker_value = mqttbroker.value
            self.mqtt_clients[device.name] = {
                'name': device.name,
                'connected': False,
                'host': broker_value['host'] if 'host' in broker_value else '127.0.0.1',
                'port': broker_value['port'] if 'port' in broker_value else '1883',
                'user': broker_value['user'] if 'user' in broker_value else None,
                'password': broker_value['password'] if 'password' in broker_value else None,
                'node_data': device,
                'client': None
            }

        for c in self.mqtt_clients.values():
            self.mqtt_connect(c)

    def _stop(self):
        for c in self.mqtt_clients.values():
            self.mqtt_disconnect(c)
        self.is_stop = True

    def start(self):
        self._start()
        super(FileReceiverPluginClient, self).start(True)

    def stop(self):
        self._stop()
        super(FileReceiverPluginClient, self).stop()

    def getstate(self, name=None):
        return {
            'code': ReturnCodes.Good,
            'data': json.dumps(self.get_client_state(name))
        }

    def is_client_connected(self, name):
        if name:
            c = self.mqtt_clients.get(name, None)
            if c:
                return c['connected']
        return False

    def get_client_state(self, name):
        res = []
        client_list = []
        if name:
            c = self.mqtt_clients.get(name, None)
            if c:
                client_list.append(c)
        else:
            client_list = self.mqtt_clients.values()

        for client in client_list:
            res.append(json.dumps({
                'name': client['name'],
                'connected': client['connected'],
                'host': client['host'],
                'port': client['port'],
            }))

        return res

    def restart(self, name):
        if name:
            c = self.mqtt_clients.get(name, None)
            if c:
                self.mqtt_connect(c)
                self.mqtt_disconnect(c)
        else:
            self._stop()
            self._start()

    def traversal(self, file_path):
        curdir = os.path.abspath(self.folder_path)
        reqdir = os.path.abspath(file_path)
        prefix = os.path.commonprefix([reqdir, curdir])
        return prefix != curdir

    def fread(self, filename):
        file_path = self.folder_path + '/' + filename
        if self.traversal(file_path):
            logger.info("file path error: ", file_path)
            return {
                'code': ReturnCodes.PLUGIN_ParamError,
                'data': 'File Name Error'}
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

    def plugin_call(self, method, msg):
        json_out = super(
            FileReceiverPluginClient,
            self).plugin_call(
            method,
            msg)
        if json_out is None:
            func = getattr(self, method)
            json_out = func(msg)
        return json_out

    def plugin_poll(self):
        for device in self.mqtt_devices:
            msg = 'online'
            if not self.is_client_connected(device.name):
                msg = 'offline'
            self.pub_event(device.name, msg, '')

    def mqtt_connect(self, mqtt_c):
        logger.debug('mqtt plugin connecting the broker......')
        node_data = mqtt_c['node_data']
        client = mqtt.Client(userdata=node_data)
        client.on_connect = self.mqtt_on_connect
        client.on_disconnect = self.mqtt_on_disconnect
        client.on_message = self.mqtt_on_message

        if mqtt_c['user'] is not None:
            client.username_pw_set(
                username=mqtt_c['user'],
                password=mqtt_c['password'])

        client.connect(mqtt_c['host'], int(mqtt_c['port']), 60)
        client.loop_start()
        mqtt_c['client'] = client

    def mqtt_disconnect(self, mqtt_c):
        if mqtt_c['client']:
            mqtt_c['client'].loop_stop()

    def mqtt_on_connect(self, client, userdata, flags, rc):
        device_node = userdata
        datatopic = self.entity.get_property(device_node, 'Mqtt Topic')
        if datatopic is not None:
            client.subscribe(datatopic.value, 0)

        self.mqtt_clients[device_node.name]['connected'] = True
        logger.info(
            'mqtt plugin connected the broker (%s) success' %
            device_node.name)

    def mqtt_on_disconnect(self, client, userdata, rc):
        device_node = userdata
        self.mqtt_clients[device_node.name]['connected'] = False
        logger.info(
            'mqtt plugin disconnect the broker (%s)' %
            device_node.name)

    def mqtt_on_message(self, client, userdata, msg):
        logger.debug(msg.topic + ":" + str(msg.payload.decode()))
        logger.debug(msg.topic + ":" + msg.payload.decode())

        device_node = userdata
        message_str = msg.payload.decode()
        node = self.entity.get_node_by_val(msg.topic, device_node)
        pair_variable = node.get_pair_friend()
        self.pub_data(device_node.name, pair_variable.name, message_str)


def plugin_main(*args, **kwargs):
    plugin_entity = FileReceiverPluginEntity(args[0])
    plugin_config = FileReceiverPluginConfig(args[1])
    plugin_client = FileReceiverPluginClient(plugin_entity, plugin_config)
    plugin_client.start()
