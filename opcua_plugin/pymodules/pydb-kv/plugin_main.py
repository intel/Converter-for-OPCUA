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
import os
import json
import leveldb
from client import BasePluginClient
from entity import BasePluginEntity
from config import BasePluginConfig
from ret_codes import ReturnCodes
from logservice.logservice import LogService

logger = LogService.getLogger(__name__)


class KvPluginEntity(BasePluginEntity):
    def __init__(self, file_name):
        super(KvPluginEntity, self).__init__(file_name)


class KvPluginConfig(BasePluginConfig):
    def __init__(self, config_fp):
        super(KvPluginConfig, self).__init__(config_fp)


class KvPluginClient(BasePluginClient):
    def __init__(self, entity, config):
        super(KvPluginClient, self).__init__(entity, config)
        self.plugin_node = self.entity.get_custom_nodes()[0]
        self.db = None

    def _start(self):
        logger.debug('leveldb plugin opening the db......')
        folder_name = self.entity.get_property(
            self.plugin_node, 'DBFileFolder').value
        db_folder = os.path.split(os.path.realpath(__file__))[
            0] + '/' + folder_name
        try:
            self.db = leveldb.LevelDB(db_folder)
            logger.info('leveldb plugin open the db success')
        except BaseException:
            self.db = None
            logger.exception('create level db failed')

    def _stop(self):
        if self.db:
            del self.db
            self.db = None
            logger.info('leveldb plugin close the db')

    def start(self):
        self._start()
        super(KvPluginClient, self).start()

    def stop(self):
        self._stop()
        super(KvPluginClient, self).stop()

    def restart(self, *args, **kwargs):
        self._stop()
        self._start()

    def is_client_connected(self, *args, **kwargs):
        return True if self.db else False

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

    def put(self, key, value):
        ret_code = 0
        result = "OK"

        try:
            self.db.Put(self.to_bytes(key), self.to_bytes(value))
            ret_code = ReturnCodes.Good
        except Exception as err:
            logger.exception('put method error')
            result = repr(err)

        return {'code': ret_code, 'data': result}

    def get(self, key):
        ret_code = 0
        try:
            result = self.db.Get(self.to_bytes(key))
            result = str(result, encoding='utf-8')
            ret_code = ReturnCodes.Good
        except KeyError as e:
            logger.exception('get method error')
            result = 'No find key data'
        except Exception as err:
            logger.exception('get method error')
            result = repr(err)

        return {'code': ret_code, 'data': result}

    def delete(self, key):

        ret_code = 1
        result = 'OK'

        try:
            self.db.Delete(self.to_bytes(key))
            ret_code = ReturnCodes.Good
        except Exception as err:
            logger.exception('delete method error')
            result = repr(err)

        return {'code': ret_code, 'data': result}

    def plugin_poll(self):
        msg = 'online'
        if not self.is_client_connected():
            msg = 'offline'
        self.pub_event(self.plugin_node.name, msg, '')

    @classmethod
    def to_bytes(cls, data):
        return bytes(data, encoding='utf-8')


def plugin_main(*args, **kwargs):
    plugin_entity = KvPluginEntity(args[0])
    plugin_config = KvPluginConfig(args[1])
    plugin_client = KvPluginClient(plugin_entity, plugin_config)
    plugin_client.start()
