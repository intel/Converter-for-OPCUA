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
import threading
import time
import os
import sys
import cv2
import datetime
import signal
import base64
from client import BasePluginClient
from entity import BasePluginEntity
from config import BasePluginConfig

from ObjectWrapper import ObjectWrapper
from flask import Flask, render_template, Response
from logservice.logservice import LogService
from ret_codes import ReturnCodes

logger = LogService.getLogger(__name__)


class WebcamVideoStream:
    def __init__(self, src, width, height):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        (self.result, self.frame) = self.stream.read()

        self.is_stop = False

    def start(self):
        threading.Thread(target=self.update, args=()).start()
        return self

    def update(self):
        while True:
            if self.is_stop:
                return

            (self.result, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.is_stop = True

# Add plugin specific config parser,refer to pymqtt/plugin_main.py


class HDPluginEntity(BasePluginEntity):
    def __init__(self, file_name):
        super(HDPluginEntity, self).__init__(file_name)


class HDPluginConfig(BasePluginConfig):
    def __init__(self, config_fp):
        super(HDPluginConfig, self).__init__(config_fp)


# Add plugin specific operations, refer to pymqtt/plugin_main.py
class HDPluginClient(BasePluginClient):
    def __init__(self, entity, config):
        super(HDPluginClient, self).__init__(entity, config)
        self.clients = []
        self.is_stop = False
        self._main = None
        self.graph_path = os.path.split(os.path.realpath(__file__))[0]
        try:
            self.detector = ObjectWrapper(self.graph_path + '/graph')
        except Exception as e:
            self.detector = None
            logger.exception('Load ObjectWrapper Failed')
            raise e
        self.new_image = None
        self.new_image_available = False
        self.lock = threading.Lock()

    def start(self):
        nodes = self.entity.get_custom_nodes()
        for node in nodes:
            try:
                src = self.entity.get_property(node, 'id')
                width = self.entity.get_property(node, 'width')
                height = self.entity.get_property(node, 'height')
                client = WebcamVideoStream(
                    src.value, width.value, height.value).start()
                client_param = {
                    'device': node,
                    'client': client,
                    'value': None}
                self.clients.append(client_param)
            except BaseException:
                logger.exception(
                    "HDPlugin: Failed to connect camera with id, %s", src)

        self._main = threading.Thread(target=self._plugin_main, args=(None,))
        self._main.setDaemon(True)
        self._main.start()
        super(HDPluginClient, self).start(True)

        flask_server = Flask(__name__)

        @flask_server.route('/')
        def index():
            return render_template('index.html')

        @flask_server.route('/video_feed')
        def video_feed():
            return Response(
                self.get_result(),
                mimetype='multipart/x-mixed-replace; boundary=frame')

        flask_server.run(host='127.0.0.1', threaded=True)

    def get_result(self):
        frame = None
        while True:
            if self.new_image_available is True:
                ret, jpeg = cv2.imencode('.jpg', self.new_image)
                frame = jpeg.tobytes()
                self.new_image_available = False
            if frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    def stop(self):
        self.is_stop = True
        # self._main.join()
        super(HDPluginClient, self).stop()
        for client in self.clients:
            video = client['client']
            video.stop()
        # TBD, currently no APIs can be used to exit the flask app,
        # one solution is to fock a new process, and kill that process,
        # but the result should be the same
        os.kill(os.getpid(), signal.SIGKILL)

    def refresh(self, msg):
        for client in self.clients:
            device_node = client['device']
            node = self.entity.get_property(device_node, 'id')
            self.lock.acquire()
            detected = client['value']
            self.lock.release()
            self.notify_data(str(detected), node)
        return {'code': ReturnCodes.Good, 'data': 'Success'}

    def plugin_poll(self):
        # TBD to add mechanim to check real device health status
        for client in self.clients:
            self.pub_event(client['device'].name, 'online', '')

    def notify_data(self, data, node):
        if data is not None:
            pair_variable = node.get_pair_friend()
            parent = node.get_parent()
            self.pub_data(parent.name, pair_variable.name, data)

    def _plugin_main(self, *args, **kwargs):
        detected = 0
        last = datetime.datetime.now()
        while not self.is_stop:
            for client in self.clients:
                device_node = client['device']
                period_node = self.entity.get_property(device_node, 'period')
                if period_node is None:
                    continue
                try:
                    video = client['client']
                    image = video.read()
                    out_image = image.copy()
                    results = self.detector.Detect(image)
                    detected = 0
                    for result in results:
                        if result.name == 'person':
                            detected += 1
                            clr = (255, 69, 0)
                            txt = result.name + " #" + \
                                str(detected) + " - (" + '%.2f%%' % (result.confidence * 100) + ")"
                            left = result.left
                            top = result.top
                            right = result.right
                            bottom = result.bottom
                            cv2.rectangle(
                                out_image, (left, top), (right, bottom), clr, thickness=3)
                            cv2.rectangle(
                                out_image, (left, top - 20), (right, top), (255, 255, 255), -1)
                            cv2.putText(
                                out_image, txt, (left + 5, top - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.5, clr, 1)
                    if not self.new_image_available:
                        self.new_image = out_image
                        self.new_image_available = True
                    self.lock.acquire()
                    client['value'] = detected
                    self.lock.release()
                except Exception as e:
                    logger.exception("HDPlugin: Failed")

                now = datetime.datetime.now()
                if (now - last) >= datetime.timedelta(0, period_node.value):
                    last = now
                    node = self.entity.get_property(device_node, 'id')
                    self.notify_data(str(detected), node)


def plugin_main(*args, **kwargs):
    plugin_entity = HDPluginEntity(args[0])
    plugin_config = HDPluginConfig(args[1])
    plugin_client = HDPluginClient(plugin_entity, plugin_config)
    plugin_client.start()
