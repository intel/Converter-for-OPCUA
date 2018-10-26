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
import json
import time
import requests
import queue
import threading

from client import BasePluginClient
from entity import BasePluginEntity
from config import BasePluginConfig
from ret_codes import ReturnCodes
from logservice.logservice import LogService

logger = LogService.getLogger(__name__)

print = sys.stderr.write


class TimeoutStreamReader(object):
    def __init__(self, stream):
        self._s = stream
        self._q = queue.Queue()

        def _proxy(stream, queue):
            while True:
                line = stream.readline()
                if line:
                    queue.put(line)

        self._t = threading.Thread(target=_proxy, args=(self._s, self._q))
        self._t.daemon = True
        self._t.start()

    def readline(self, timeout=None):
        try:
            return self._q.get(block=True, timeout=timeout)
        except queue.Empty:
            return None


class PluginRequestTimeout(Exception):
    pass


class PluginRequestDataError(Exception):
    pass


class UnexpectedEndOfStream(Exception):
    pass


class ManagerPluginEntity(BasePluginEntity):
    def __init__(self, file_name):
        super(ManagerPluginEntity, self).__init__(file_name)


class ManagerPluginConfig(BasePluginConfig):
    def __init__(self, config_fp):
        super(ManagerPluginConfig, self).__init__(config_fp)


class ManagerPluginClient(BasePluginClient):

    def __init__(self, entity, config):
        super(ManagerPluginClient, self).__init__(entity, config)
        self.manage_q = None
        self.rfile = TimeoutStreamReader(sys.stdin)
        self.wfile = sys.stdout
        self.request_id = 0

    def injection_manage_q(self, q):
        self.manage_q = q

    def _start(self):
        logger.debug('ManagerPlugin plugin start......')

    def _stop(self):
        pass

    def start(self):
        self._start()
        super(ManagerPluginClient, self).start()

    def stop(self):
        self._stop()
        super(ManagerPluginClient, self).stop()

    def restart(self, *args, **kwargs):
        self._stop()
        self._start()

    def get_plugin_list(self):
        ret_code = 1
        req_data = {
            'action': 'get_plugin_list',
            'data': [],
        }
        try:
            res = self.request(req_data)
            result = json.dumps(res)
            ret_code = 0
        except PluginRequestTimeout as te:
            result = "Request Timeout"
        except PluginRequestDataError as de:
            result = "Server Response Data Error"
        except Exception as e:
            result = repr(e)
        return {'code': ret_code, 'data': result}

    def start_plugin(self, name):
        ret_code = 1
        req_data = {
            'action': 'start_plugin',
            'data': [name],
        }
        try:
            res = self.request(req_data)
            result = json.dumps(res)
            ret_code = 0
        except PluginRequestTimeout as te:
            result = "Request Timeout"
        except PluginRequestDataError as de:
            result = "Server Response Data Error"
        except Exception as e:
            result = repr(e)
        return {'code': ret_code, 'data': result}

    def stop_plugin(self, name):
        ret_code = 1
        req_data = {
            'action': 'stop_plugin',
            'data': [name],
        }
        try:
            res = self.request(req_data)
            result = json.dumps(res)
            ret_code = 0
        except PluginRequestTimeout as te:
            result = "Request Timeout"
        except PluginRequestDataError as de:
            result = "Server Response Data Error"
        except Exception as e:
            result = repr(e)
        return {'code': ret_code, 'data': result}

    def getcfg(self, name, cfg_type):
        ret_code = 1
        req_data = {
            'action': 'getcfg',
            'data': [name, cfg_type],
        }
        try:
            res = self.request(req_data)
            result = json.dumps(res)
            ret_code = 0
        except PluginRequestTimeout as te:
            result = "Request Timeout"
        except PluginRequestDataError as de:
            result = "Server Response Data Error"
        except Exception as e:
            result = repr(e)
        return {'code': ret_code, 'data': result}

    def setcfg(self, name, cfg_type, s):
        ret_code = 1
        req_data = {
            'action': 'setcfg',
            'data': [name, cfg_type, s],
        }
        try:
            res = self.request(req_data)
            result = json.dumps(res)
            ret_code = 0
        except PluginRequestTimeout as te:
            result = "Request Timeout"
        except PluginRequestDataError as de:
            result = "Server Response Data Error"
        except Exception as e:
            result = repr(e)
        return {'code': ret_code, 'data': result}

    def is_client_connected(self, *args, **kwargs):
        return True

    def get_client_state(self, *args, **kwargs):
        return {
            'name': self.entity.get_property(
                self.plugin_node,
                'DBFileFolder').value,
            'connected': self.is_client_connected(),
        }

    def getstate(self, *args, **kwargs):
        return {
            'code': ReturnCodes.Good,
            'data': json.dumps(self.get_client_state())
        }

    def plugin_poll(self):
        msg = 'online'
        self.pub_event('', msg, '')

    def request(self, req):
        req_id = self.request_id
        self.request_id += 1
        req.update({'request_id': req_id})
        self.send(req)
        return self.recv(req_id)

    def recv(self, req_id, timeout=5):
        flag = True
        end_time = time.time() + timeout
        while flag:
            remaining = end_time - time.time()
            if remaining <= 0.0:
                raise PluginRequestTimeout

            res = self.rfile.readline(timeout=1)
            if res:
                try:
                    data = json.loads(res)
                except BaseException:
                    raise PluginRequestDataError

                if data:
                    reply_id = data.get('request_id', None)
                    if reply_id == req_id:
                        return data.get('result')
                    elif reply_id < req_id:
                        continue
                    else:
                        raise PluginRequestDataError

    def send(self, data):
        if self.wfile:
            self.wfile.write(json.dumps(data))
            self.wfile.write('\n')
            self.wfile.flush()


def plugin_main(*args, **kwargs):
    plugin_entity = ManagerPluginEntity(args[0])
    plugin_config = ManagerPluginConfig(args[1])
    plugin_client = ManagerPluginClient(plugin_entity, plugin_config)
    plugin_client.start()
