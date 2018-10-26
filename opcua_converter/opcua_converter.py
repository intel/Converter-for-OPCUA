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
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(BASE_DIR, 'opcua_plugin'))
sys.path.append(os.path.join(BASE_DIR, 'pyutilities'))

# sys.path.append("../opcua_plugin")
# sys.path.append("../pyutilities")

#from logservice.logservice import LogService
from security.config_security import UaSecurity
from storage.config_storage import UaStorage
from logger.ua_logger import UaLogger

import time
import logging
import json
import threading
import datetime

try:
    from IPython import embed
except ImportError:
    import code

    def embed():
        vars = globals()
        vars.update(locals())
        shell = code.InteractiveConsole(vars)
        shell.interact()
from opcua import ua, Server
from jsonimporter import JsonImporter
from plugin_adapter import PlugInAdapter

logger = logging.getLogger()


class SubHandler(object):
    """
    Subscription Handler. To receive events from plugin
    """

    IDLE_WAIT = 1
    HEARTBEAT_WAIT = 30

    def __init__(self, server, adapter):
        self.server = server
        self.adapter = adapter
        self.plugins = {}
        self._thread = None

    def loop(self):
        delete_list = []
        now = datetime.datetime.now()
        for name, p in self.plugins.items():
            if (now - p.get('last_time')).total_seconds() > self.HEARTBEAT_WAIT:
                delete_list.append(name)

        for d in delete_list:
            self._delete_plugin(d)

    def main(self):
        while True:
            time.sleep(self.IDLE_WAIT)
            self.loop()

    def run(self):
        if not self._thread:
            self._thread = threading.Thread(target=self.main, args=())
            self._thread.setDaemon(True)
            self._thread.start()

    def _online(self, plugin_name):
        p = self.plugins.get(plugin_name, None)
        if not p:  # first online.
            self.plugins[plugin_name] = {
                'node': None,
                'last_time': datetime.datetime.now(),
            }

        else:  # second online
            node = p.get('node', None)
            if not node:
                now = datetime.datetime.now()
                if (now - p.get('last_time')
                        ).total_seconds() > 1:  # maybe third online
                    plugin_node = None
                    objects = self.server.get_objects_node().get_children()
                    for object in objects:
                        if object.get_display_name().to_string() != "Server":
                            if plugin_name in object.get_display_name().to_string():
                                plugin_node = object
                                break
                    if not plugin_node:
                        self.load_rd(plugin_name)
                    else:
                        p['node'] = plugin_node
            else:
                p['last_time'] = datetime.datetime.now()

    def _delete_plugin(self, plugin_name):
        p = self.plugins.get(plugin_name, None)
        if p:
            plugin_node = p.get('node', None)
            if plugin_node:
                self.server.delete_nodes([plugin_node, ], recursive=True)
            del self.plugins[plugin_name]

    def load_rd(self, plugin_name):
        json_in = {'method': 'getrd'}
        retcode, json_out = self.adapter.plugin_call(plugin_name, json_in)
        if retcode == 0 and json_out:
            logger.debug('json_out:' + json.dumps(json_out))
            json_data = json.loads(json_out['data'])
            file_name = '.plugin_' + plugin_name + '.json'
            f = open(file_name, 'wb')
            f.write(json.dumps(json_data).encode('utf-8'))
            f.close()
            # import some nodes from json
            importer = JsonImporter(self.server, self.adapter, plugin_name)
            importer.import_json(file_name)

        else:
            logger.error('get resource fail to plugin:' + plugin_name)

    def set_value(self, parent, dev_name, var_name, data, it_level=0):
        if parent is None:
            return
        nodes = parent.get_children()
        for node in nodes:
            if dev_name in node.get_display_name().to_string():
                sub_nodes = node.get_children()
                for var in sub_nodes:
                    if var_name == var.get_display_name().to_string():
                        logger.debug("    Dev Name: " + dev_name)
                        logger.debug("    Var Name: " + var_name)
                        logger.debug("    Var Data: " + str(data))
                        if len(data):
                            var.set_value(data)
                            return True
                return True
            else:
                it_level += 1
                if it_level > 1 or node.get_node_class() is not ua.NodeClass.Object:
                    pass
                elif self.set_value(node, dev_name, var_name, data, it_level) is True:
                    return True
        return False

    def datachange_notification(self, plugin_name, dev_name, var_name, data):
        objects = self.server.get_objects_node().get_children()
        logger.debug('datachange_notification:')
        for object in objects:
            if object.get_display_name().to_string() != "Server":
                if plugin_name in object.get_display_name().to_string():
                    logger.debug("New data change Event:")
                    logger.debug("    Node: " + plugin_name)
                    self.set_value(object, dev_name, var_name, data)

    def event_notification(self, plugin_name, dev_name, event_name, data):
        if event_name == 'online':
            self._online(plugin_name)
        elif event_name == 'exit':
            self._delete_plugin(plugin_name)
        else:
            pass


def ConfigHistoryStorage(server):
    uastorage = UaStorage()
    dbtype = uastorage.get_storagetype()

    if dbtype == 'sqlite':
        dbmodule = __import__(
            'opcua.server.history_sql',
            fromlist=['HistorySQLite'])
        server.iserver.history_manager.set_storage(
            dbmodule.HistorySQLite(uastorage.get_sqliteconfig()))
    elif dbtype == 'mongo':
        dbmodule = __import__('history_mongo', fromlist=['HistoryMongo'])
        host, port, path = uastorage.get_mongoconfig()
        server.iserver.history_manager.set_storage(
            dbmodule.HistoryMongo(host, port, path))


def opcua_converter_main(options):
    # setup our server
    server = Server()
    uasecurity = UaSecurity()
    if uasecurity.get_securitytype() == 'tls':
        server_cert, client_cert, private_key = uasecurity.get_certificates()
        if server_cert is None:
            logger.error(
                'tls is enabled, but server cert is missing with current configuration')
            sys.exit(-1)
        if private_key is None:
            logger.error(
                'tls is enabled, but private key is missing with current configuration')
            sys.exit(-1)
        server.load_certificate(server_cert)
        server.load_private_key(private_key)
    ConfigHistoryStorage(server)
    server.start()

    # setup adapter
    adapter = PlugInAdapter(options.conf_file)
    handler = SubHandler(server, adapter)
    handler.run()
    adapter.subscription(
        handler.datachange_notification,
        handler.event_notification)
    adapter.start()

    try:
        while True:
            logger.debug('opcua converter running......')
            time.sleep(60)
    finally:
        # close connection, remove subcsriptions, etc
        adapter.stop()
        server.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='opcua converter arguments')
    parser.add_argument(
        '-c',
        '--conf',
        dest='conf_file',
        action='store',
        default=None,
        help='opcua converter configurate file')
    parser.add_argument(
        '-l',
        '--loglevel',
        dest='log_level',
        action='store',
        default=None,
        help='log level: critical/error/warning/info/debug')
    parser.add_argument(
        '-o',
        '--output',
        dest='output',
        action='store',
        default=None,
        help='log output file with path')
    parser.add_argument(
        '-s',
        '--console',
        action="store_true",
        help='true is enable to print out log in console')
    (options, args) = parser.parse_known_args()
    if options.conf_file:
        ualogger = UaLogger(logger, options.conf_file)
    else:
        ualogger = UaLogger(logger)
    if options.log_level:
        ualogger.set_loggerlevel(options.log_level)
    if options.output:
        ualogger.set_loggerpath(options.output)
    if options.console:
        ualogger.enable_console()
    ualogger.enable_logger('opcua_converter.log')

    # LogService.initialize()
    opcua_converter_main(options)
