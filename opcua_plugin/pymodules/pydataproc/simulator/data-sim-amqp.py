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

import time

import logging
# logging.basicConfig(level=logging.DEBUG)

from amqpstorm import Connection
from amqpstorm import Message

DATA_FILE = 'measurement_data.jsonl'
AMQP_HOST = 'localhost'
AMQP_USER = 'guest'
AMQP_PASSWORD = 'guest'
AMQP_QUEUE = 'source_test'
# should be the same as queue name when using default exchange
AMQP_ROUTING_KEY = 'source_test'


def send_amqp_data():
    with Connection(AMQP_HOST, AMQP_USER, AMQP_PASSWORD) as connection:
        with connection.channel() as channel:
            try:
                channel.queue.declare(AMQP_QUEUE)

                with open(DATA_FILE) as file:
                    for line in file:
                        line = line.strip('\n')
                        message = Message.create(channel, line)
                        message.content_type = 'application/json'
                        message.publish(routing_key=AMQP_ROUTING_KEY)
                        print("Sending message: {}".format(line))
                        time.sleep(1)
            except BaseException:
                channel.close()


if __name__ == '__main__':
    send_amqp_data()
