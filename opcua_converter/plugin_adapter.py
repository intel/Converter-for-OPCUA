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
#
# -----------------------------

import sys
import threading
from mqservice import MsgQueueService
from ret_codes import ReturnCodes
from security.config_security import UaAmqpSecurity
from configger.config_parser import ConfigLoader


class PlugInAdapter(object):
    def __init__(self, credential=None):
        self.name = 'opcua'
        self.data_callback = None
        self.event_callback = None

        if credential is None:
            self.config = ConfigLoader()
        else:
            self.config = ConfigLoader(credential)

        self.configdict = self.config.ConfigSectionMap('Amqp')
        self.mq_serv = MsgQueueService(
            self.name,
            self.configdict['url'],
            threading.Lock(),
            tls_config=UaAmqpSecurity().get_tls_confg()
        )

    def _recv(self, json_in):
        if self.data_callback and 'data' in json_in.keys():
            plugin_name = json_in['data'][0]
            device_name = json_in['data'][1]
            var_name = json_in['data'][2]
            var_data = json_in['data'][3]
            self.data_callback(plugin_name, device_name, var_name, var_data)

        if self.event_callback and 'event' in json_in.keys():
            plugin_name = json_in['event'][0]
            device_name = json_in['event'][1]
            event_name = json_in['event'][2]
            event_data = json_in['event'][3]
            self.event_callback(
                plugin_name,
                device_name,
                event_name,
                event_data)

    def start(self):
        # TBD, use try to cather the error
        self.mq_serv.set_callback(self._recv)
        self.mq_serv.start()

    def stop(self):
        self.mq_serv.stop()

    def plugin_setvar(self, plugin_name, json_in):
        self.mq_serv.publish(plugin_name, json_in)

    def plugin_call(self, plugin_name, json_in):
        res = self.mq_serv.request(plugin_name, json_in, timeout=4)
        if res is None:
            return 0, {'code': ReturnCodes.PLUGIN_RpcError,
                       'data': 'rpc request error'}
        return 0, res

    def subscription(self, data_callback, event_callback):
        self.data_callback = data_callback
        self.event_callback = event_callback
