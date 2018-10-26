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
import time
import platform
import threading
import signal
import json
from base64 import b64decode
from mqservice import MsgQueueService
from logservice.logservice import LogService
from ret_codes import ReturnCodes

logger = LogService.getLogger(__name__)


class BasePluginClient(object):
    def __init__(self, entity, config):
        self.name = entity.plugin_name
        self.thread_monitor = None
        self.monitor_wait = 1.0
        self.monitor_finish_evt = threading.Event()
        # Use threading.Event for further potential event trigger usage
        self.sigterm = threading.Event()
        self.entity = entity
        self.config = config
        self.methods = self.entity.get_methods()

        url = None
        if self.config.fetch_mq_env():
            url = self.config.fetch_mq_env()['url']

        self.mq_serv = MsgQueueService(
            self.name,
            url=url,
            req_lock=threading.Lock(),
            tls_config=self.config.fetch_security_env()
        )
        LogService.initialize(**(self.config.fetch_logger_env() or {}))

    def sys_handler(self, signum, frame):
        logger.info('Exiting plugin process ... name:%s', self.name)
        self.stop()

    def start(self, daemon=False):
        logger.debug('Loading plugin process ... name:%s', self.name)

        self.thread_monitor = threading.Thread(
            target=self._thread_monitor, args=(None,))
        self.thread_monitor.setDaemon(True)
        self.thread_monitor.start()

        self.mq_serv.set_callback(self._recv, self._notify)
        logger.info('Loading plugin process finish ... name:%s', self.name)

        self.mq_serv.start()
        signal.signal(signal.SIGTERM, self.sys_handler)
        signal.signal(signal.SIGINT, self.sys_handler)

        logger.info('Loading plugin process start ... name:%s', self.name)
        signal.pause()

    def stop(self):
        self.sigterm.set()
        self.monitor_finish_evt.set()
        self.thread_monitor.join()
        self.pub_event('', 'exit', '')
        self.mq_serv.stop()
        self.sigterm.clear()
        logger.info('Exited plugin process ... name:%s', self.name)

    def is_alive(self):
        return not self.sigterm.is_set()

    def pub_data(self, dev_name, var_name, var_data):
        json_out = {
            'data': [self.name, dev_name, var_name, var_data]
        }
        try:
            if self.mq_serv:
                self.mq_serv.publish('opcua', json_out)
        except BaseException:
            pass

    def pub_event(self, dev_name, evt_name, evt_data):
        json_out = {
            'event': [self.name, dev_name, evt_name, evt_data]
        }
        try:
            if self.mq_serv:
                self.mq_serv.publish('opcua', json_out)
        except BaseException:
            pass

    def getrd(self):
        return {'code': ReturnCodes.Good, 'data': json.dumps(self.entity.data)}

    def ping(self):
        return {'code': ReturnCodes.Good, 'data': 'pong'}

    def getstate(self, name=None):
        return {'code': ReturnCodes.PLUGIN_ParamError,
                'data': 'No yet implemented in this Plugin'}

    def refresh(self):
        return {'code': ReturnCodes.PLUGIN_ParamError,
                'data': 'No yet implemented in this Plugin'}

    def download(self, file_name, file_str):
        file_path = os.path.split(os.path.realpath(self.entity.file_name))[
            0] + '/' + file_name
        file = open(file_path, 'wb')
        file.write(b64decode(file_str))
        file.close()
        json_out = {'code': ReturnCodes.Good, 'data': "Success"}
        return json_out

    def _prepare_methods(self, method, input_list):
        m = self.methods.get(method, None)
        args = []
        if not m:
            return False, args, 'the method is not defined'

        flag, args, msg = m.check_inputs(input_list)
        if not flag:
            return False, [], msg

        return True, args, 'OK'

    def plugin_call(self, method, msg):
        flag, args, msg = self._prepare_methods(method, msg)
        if not flag:
            return {'code': ReturnCodes.PLUGIN_ParamError, 'data': msg}
        if hasattr(self, method):
            func = getattr(self, method)
            if callable(func):
                try:
                    return func(*args)
                except BaseException:
                    logger.exception('method execute error')
                    return {
                        'code': 500,
                        'data': 'unknown method execute error'}
        return {
            'code': ReturnCodes.PLUGIN_ParamError,
            'data': 'method not implemented'}

    def plugin_poll(self):
        custom_objs = self.entity.get_custom_nodes()
        if len(custom_objs) == 0:
            try:
                self.pub_event('', 'online', '')
            except BaseException:
                pass
        for obj in custom_objs:
            try:
                self.pub_event(obj.name, 'online', '')
            except BaseException:
                pass

    def _do_write_variable(self, data):
        variable_name = data['variable_name']
        value = data['data']

    def _recv(self, json_in):
        if 'method' in json_in:
            method = json_in['method'] if 'method' in json_in else None
            data = json_in['data'] if 'data' in json_in else None
            json_out = self.plugin_call(method, data)
            return json_out
        else:
            logger.info('incorrect client request. %s' % json.dumps(json_in))

    def _notify(self, json_in):
        if 'variable' in json_in:
            self._do_write_variable(json_in)
        else:
            logger.info('incorrect client request. %s' % json.dumps(json_in))

    def _thread_monitor(self, *args, **kwargs):
        while self.is_alive():
            self.monitor_finish_evt.wait(self.monitor_wait)
            try:
                self.plugin_poll()
                if self.monitor_wait < 5:
                    self.monitor_wait += 1
            except BaseException:
                logger.exception('plugin_poll error')
