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

from amqpstorm import Connection

import logging
# logging.basicConfig(level=logging.DEBUG)

AMQP_HOST = 'localhost'
AMQP_USER = 'guest'
AMQP_PASSWORD = 'guest'
AMQP_QUEUE = 'sink_test'
# should be the same as queue name when using default exchange
AMQP_ROUTING_KEY = 'sink_test'


def on_message(message):
    print("Received message:", message.body)
    message.ack()


def start_monitor():
    with Connection(AMQP_HOST, AMQP_USER, AMQP_PASSWORD) as connection:
        with connection.channel() as channel:
            channel.queue.declare(AMQP_QUEUE)
            channel.basic.consume(on_message, AMQP_QUEUE, no_ack=False)

            try:
                channel.start_consuming()
            except KeyboardInterrupt:
                channel.close()


if __name__ == '__main__':
    start_monitor()
