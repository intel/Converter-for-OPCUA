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
import json
import sys
import time
import threading

from logservice.logservice import LogService

logger = LogService.getLogger(__name__)

if sys.version_info.major >= 3:
    from mqservice.amqp import AMQPConn
    from urllib.parse import urlparse
    from queue import Queue as Q
else:
    from amqp import AMQPConn
    from urlparse import urlparse
    from Queue import Queue as Q


class MsgQueueService(threading.Thread):
    def __init__(self, queue_name, url=None, req_lock=None, tls_config=None):
        super(MsgQueueService, self).__init__()
        if url is None:
            self.host = '127.0.0.1'
            self.username = 'guest'
            self.password = 'guest'
        else:
            self.server_url = urlparse(url)
            self.host = self.server_url.hostname
            self.username = self.server_url.username
            self.password = self.server_url.password

        self.queue_name = queue_name
        self.req_lock = req_lock
        self.tls_config = tls_config
        self.publish_q = Q()
        self.notif_callback = None
        self.request_callback = None
        self._running = threading.Event()

    def _start(self, daemon=False):
        try:
            self.conn = AMQPConn(
                self.host,
                self.username,
                self.password,
                self.queue_name,
                self.req_lock,
                self.tls_config,
            )
        except BaseException:
            return False
        self.conn.set_callback(self.on_request, self.on_notify)
        try:
            self.conn.start(daemon)
        except BaseException:
            self.conn.stop()
            return False

        self._running.set()
        return True

    def stop(self):
        if self._running.is_set():
            self.conn.stop()
            self._running.clear()

    def request(self, remote_queue, req_json, timeout=0):
        res = self.conn.request(remote_queue, req_json, timeout)
        if isinstance(res, str):
            try:
                res = json.loads(res)
            except BaseException:
                logger.exception("rpc response format error")
                res = None
        elif res is None:
            logger.error("rpc response timeout")
        else:
            logger.error("unknown rpc error")
        return res

    def publish(self, remote_queue, req_json):
        self.publish_q.put({'queue_name': remote_queue, 'data': req_json})

    def on_request(self, message):
        if self.request_callback:
            return self.request_callback(message)

    def on_notify(self, message):
        if self.notif_callback:
            self.notif_callback(message)

    def set_callback(self, request_callback, notif_callback=None):
        self.request_callback = request_callback
        if self.notif_callback is None:
            self.notif_callback = request_callback

    def run(self):
        count = 0
        while (not self._start(True)) and (count < 10):
            time.sleep(1)
            count += 1

        while self._running.is_set():
            request = None
            try:
                request = self.publish_q.get(block=True, timeout=1.1)
            except BaseException:
                pass
            if request:
                self.conn.publish(request['queue_name'], request['data'])
        if count >= 10:
            logger.error(
                "the amqp connect failed, and the application start failed.")
