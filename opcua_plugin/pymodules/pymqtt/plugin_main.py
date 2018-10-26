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
import ssl
import hashlib
import paho.mqtt.client as mqtt
from ret_codes import ReturnCodes
from logservice.logservice import LogService

logger = LogService.getLogger(__name__)


class MqttPluginEntity(BasePluginEntity):
    def __init__(self, file_name):
        super(MqttPluginEntity, self).__init__(file_name)

    def get_logger():
        return super(MqttPluginEntity, self).get_logger()


class MqttPluginConfig(BasePluginConfig):
    def __init__(self, config_fp):
        super(MqttPluginConfig, self).__init__(config_fp)


class MqttPluginClient(BasePluginClient):
    def __init__(self, entity, config):
        super(MqttPluginClient, self).__init__(entity, config)
        self.mqtt_devices = self.entity.get_custom_nodes()
        self.mqtt_clients = {}

    def _start(self):
        for device in self.mqtt_devices:
            mqttbroker = self.entity.get_property(device, 'MQTT Broker')
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
                'cafile': broker_value['cafile'] if 'cafile' in broker_value else None,
                'cert': broker_value['cert'] if 'cert' in broker_value else None,
                'key': broker_value['key'] if 'key' in broker_value else None,
                'node_data': device,
                'client': None,
                'blob': None,
                'blob_hash': None
            }

        for c in self.mqtt_clients.values():
            self.mqtt_connect(c)

    def _stop(self):
        for c in self.mqtt_clients.values():
            self.mqtt_disconnect(c)

    def start(self):
        self._start()
        super(MqttPluginClient, self).start()

    def stop(self):
        self._stop()
        super(MqttPluginClient, self).stop()

    def getstate(self, name=None):
        return {
            'code': ReturnCodes.Good,
            'data': json.dumps(self.get_client_state(name))
        }

    def send(self, name, topic, msg):
        errorcode = 0
        try:
            c = self.getcli(name)
            if c is not None:
                if c['connected']:
                    c['client'].publish(topic, msg)

                    errorcode = 0
                    result = 'succeeded to send data'
                else:
                    errorcode = 1
                    result = 'the host name was not connected'
            else:
                errorcode = 1
                result = 'the host name was not initiated'
        except BaseException:
            errorcode = 1
            result = 'failed to send data'

        return {
            'code': errorcode,
            'data': result
        }

    def getcli(self, host_str):
        for client in self.mqtt_clients.values():
            if host_str == client['name']:
                return client
        return None

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

    def plugin_poll(self):
        self.pub_event('', 'online', '')

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

        if mqtt_c['cafile'] is not None:
            if os.path.exists(
                    mqtt_c['cafile']) and os.path.exists(
                    mqtt_c['cert']) and os.path.exists(
                    mqtt_c['key']):
                client.tls_set(
                    ca_certs=mqtt_c['cafile'],
                    certfile=mqtt_c['cert'],
                    keyfile=mqtt_c['key'],
                    cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLSv1,
                    ciphers=None)
            else:
                logger.info(
                    'The key files are not extists by (%s)' %
                    mqtt_c['name'])
        try:
            client.connect(mqtt_c['host'], int(mqtt_c['port']), 60)
        except BaseException:
            logger.info(
                'mqtt plugin connected the broker (%s) fail' %
                mqtt_c['name'])
        client.loop_start()
        mqtt_c['client'] = client

    def mqtt_disconnect(self, mqtt_c):
        if mqtt_c['client']:
            device_node = mqtt_c['node_data']
            datatopic = self.entity.get_property(device_node, 'Raw Topic')
            if datatopic is not None:
                mqtt_c['client'].unsubscribe(datatopic.value)

            alarmtopic = self.entity.get_property(device_node, 'Alam Topic')
            if alarmtopic is not None:
                mqtt_c['client'].unsubscribe(alarmtopic.value)

            blobtopic = self.entity.get_property(device_node, 'Blob Topic')
            if blobtopic is not None:
                mqtt_c['client'].unsubscribe(blobtopic.value)

            mqtt_c['client'].loop_stop()
            mqtt_c['client'].disconnect()

    def mqtt_on_connect(self, client, userdata, flags, rc):
        device_node = userdata
        datatopic = self.entity.get_property(device_node, 'Raw Topic')
        if datatopic is not None:
            client.subscribe(datatopic.value, 0)

        alarmtopic = self.entity.get_property(device_node, 'Alam Topic')
        if alarmtopic is not None:
            client.subscribe(alarmtopic.value, 0)

        blobtopic = self.entity.get_property(device_node, 'Blob Topic')
        if blobtopic is not None:
            client.subscribe(blobtopic.value, 0)

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
        device_node = userdata

        blobtopic = self.entity.get_property(device_node, 'Blob Topic')
        if blobtopic is not None and blobtopic.value == msg.topic:
            self.on_blob_message(userdata, msg.payload)
        else:
            logger.debug(msg.topic + ":" + str(msg.payload.decode()))
            logger.debug(msg.topic + ":" + msg.payload.decode())

            message_str = msg.payload.decode()
            node = self.entity.get_node_by_val(msg.topic, device_node)
            pair_variable = node.get_pair_friend()
            self.pub_data(device_node.name, pair_variable.name, message_str)

    def on_blob_message(self, userdata, msg):
        device_node = userdata
        fout = self.mqtt_clients[device_node.name]['blob']
        if len(msg) == 0xFF:  # is header or end
            msg_in = msg.decode()
            msg_in = msg_in.split(":")
            if msg_in[0] == "END":
                in_hash_final = self.mqtt_clients[device_node.name]['blob_hash'].hexdigest(
                )
                if in_hash_final == msg_in[1]:
                    logger.debug("File Copied OK - Valid Hash")
                else:
                    logger.error("Bad File Received - Invalid Hash")
                fout.close()
                return
            elif msg_in[0] == "START":
                file_name = msg_in[1]
                file_path = os.path.split(os.path.realpath(self.entity.file_name))[
                    0] + '/' + file_name
                self.mqtt_clients[device_node.name]['blob'] = open(
                    file_path, "wb")
                self.mqtt_clients[device_node.name]['blob_hash'] = hashlib.md5()
                return
            else:
                pass
        self.mqtt_clients[device_node.name]['blob_hash'].update(msg)
        fout.write(msg)


def plugin_main(*args, **kwargs):
    plugin_entity = MqttPluginEntity(args[0])
    plugin_config = MqttPluginConfig(args[1])
    plugin_client = MqttPluginClient(plugin_entity, plugin_config)
    plugin_client.start()
