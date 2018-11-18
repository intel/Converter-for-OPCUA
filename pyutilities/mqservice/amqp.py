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

import sys
import os
import time
import ssl
import threading
import amqpstorm
import json
import datetime

from amqpstorm import Message


class AMQPConn(object):
    def __init__(self, host, username, password, routing, lock, tls_config=None):
        """
        :param host: RabbitMQ Server e.g. 127.0.0.1
        :param username: RabbitMQ Username e.g. guest
        :param password: RabbitMQ Password e.g. guest
        :return:
        """

        # TBD to support SSL
        self.host = host
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self.resp_queue = None
        self.response = None
        self.correlation_id = None
        self.on_request = routing
        self.thread_main = None
        self.request_callback = None
        self.notif_callback = None
        self.tls_config = tls_config
        self.use_ssl = False

        if self.tls_config:
            if self.tls_config.get('tls', None):
                self.use_ssl = True

        self.lock = lock
        self._stopped = threading.Event()
        self.setup()

    def _on_request(self, message):
        json_in = json.loads(message.body)
        # print(json_str)
        if message.reply_to:
            if self.request_callback:
                result = self.request_callback(json_in)
                properties = {
                    'correlation_id': message.correlation_id
                }
                response = Message.create(
                    message.channel, json.dumps(
                        result, ensure_ascii=False), properties)
                response.content_type = 'application/json'
                response.publish(message.reply_to)
        else:
            if self.notif_callback:
                self.notif_callback(json_in)
        message.ack()

    def _on_response(self, message):
        if self.correlation_id != message.correlation_id:
            return
        self.response = message.body

    def setup(self):
        if self.use_ssl:
            self.connection = amqpstorm.Connection(
                self.host,
                self.username,
                self.password,
                port=5671,
                ssl=True,
                ssl_options={
                    'ssl_version': ssl.PROTOCOL_TLSv1_2,
                    'cert_reqs': ssl.CERT_REQUIRED,
                    'keyfile': self.tls_config.get('keyfile'),
                    'certfile': self.tls_config.get('cerfile'),
                    'ca_certs': self.tls_config.get('cafile'),
                }
            )
        else:
            self.connection = amqpstorm.Connection(self.host,
                                                   self.username,
                                                   self.password)
        self.channel = self.connection.channel()

        result = self.channel.queue.declare(exclusive=True)
        self.resp_queue = result['queue']
        self.channel.basic.consume(self._on_response, no_ack=True,
                                   queue=self.resp_queue)

        self.channel.queue.declare(queue=self.on_request)
        self.channel.queue.purge(queue=self.on_request)
        self.channel.basic.qos(prefetch_count=100)
        self.channel.basic.consume(self._on_request, queue=self.on_request)

    def request(self, routing_key, req_json, timeout=0):
        self.lock.acquire()
        self.response = None
        message = Message.create(
            self.channel, body=json.dumps(
                req_json, ensure_ascii=False))
        message.reply_to = self.resp_queue
        message.content_type = 'application/json'

        self.correlation_id = message.correlation_id
        message.publish(routing_key=routing_key)
        start = datetime.datetime.now()
        while not self.response:
            self.channel.process_data_events()
            time.sleep(0.01)
            now = datetime.datetime.now()
            if timeout > 0 and (now - start) >= datetime.timedelta(0, timeout):
                break
        response = self.response
        self.lock.release()
        return response

    def publish(self, routing_key, req_json):
        message = Message.create(
            self.channel, body=json.dumps(
                req_json, ensure_ascii=False))
        message.content_type = 'application/json'
        message.publish(routing_key=routing_key)

    def start(self, daemon):
        self._stopped.clear()
        if daemon is True:
            self.thread_main = threading.Thread(
                target=self._thread_main, args=(None,))
            self.thread_main.setDaemon(True)
            self.thread_main.start()
        else:
            self.channel.start_consuming()

    def stop(self):
        self._stopped.set()
        self.channel.stop_consuming()
        if self.thread_main:
            self.thread_main.join()
        self.channel.close()
        self.connection.close()

    def set_callback(self, request_callback, notif_callback):
        self.request_callback = request_callback
        self.notif_callback = notif_callback

    def _thread_main(self, *args, **kwargs):
        need_reconnect = False
        while self._stopped.is_set() is not True:
            try:
                self.channel.start_consuming()
            except amqpstorm.AMQPError:
                if self._stopped.is_set() is True:
                    break
                need_reconnect = True
                pass
            if need_reconnect is True:
                self.channel.stop_consuming()
                self.channel.close()
                self.channel = None
                self.connection.close()
                self.connection = None
                while True:
                    try:
                        self.setup()
                        break
                    except BaseException:
                        time.sleep(1)
                need_reconnect = False
