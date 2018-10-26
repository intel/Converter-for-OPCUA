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

import threading
import time
import sys
import os
import importlib

from amqpstorm import Connection
from amqpstorm import Message

import threading

from logservice.logservice import LogService
logger = LogService.getLogger(__name__)


class AmqpClient:
    def __init__(
            self,
            source_queue,
            sink_queue,
            host="localhost",
            user="guest",
            password="guest"):
        self.source_queue = source_queue
        self.sink_queue = sink_queue

        self.connection = Connection(host, user, password)
        self.channel = self.connection.channel()
        self.channel.queue.declare(source_queue)
        self.channel.queue.declare(sink_queue)

        self.process_func = None

    def set_process_func(self, func):
        self.process_func = func

    def _on_message(self, message):
        try:
            if self.process_func:
                passed, result = self.process_func(message.body)
                if passed:
                    logger.debug("Sending result: {}".format(result))
                    message = Message.create(self.channel, body=result)
                    message.content_type = 'application/json'
                    message.publish(routing_key=self.sink_queue)
            else:
                logger.debug("Received message:", message.body)

        except Exception as e:
            logger.error("Exception thrown when calling UDF!")

    def _amqp_thread(self):
        self.channel.basic.consume(self._on_message, self.source_queue)
        try:
            self.channel.start_consuming()
        except BaseException:
            self.channel.close()

    def run(self):
        self.thread = threading.Thread(target=self._amqp_thread)
        self.thread.setDaemon(True)
        self.thread.start()

    def stop(self):
        if self.channel:
            self.channel.close()


if __name__ == '__main__':

    UDF_FOLDER_PATH = os.path.dirname(os.path.realpath(__file__)) + "/udf"
    UDF_FILE_NAME = "udf_simple.py"
    UDF_FILE_PATH = UDF_FOLDER_PATH + "/" + UDF_FILE_NAME

    try:
        sys.path.insert(0, UDF_FOLDER_PATH)
        udf = importlib.import_module(os.path.splitext(UDF_FILE_NAME)[0])
        client = AmqpClient("source_test", "sink_test")
        client.set_process_func(udf.process)
        client.run()
        client.thread.join()

    except KeyboardInterrupt:
        client.channel.close()
