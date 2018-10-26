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

"""
add nodes defined in Jason to address space
format is the one from opc-ua specification
"""
import uuid
from copy import copy

import opcua
from opcua import ua, uamethod
import json
from datetime import timedelta
from datetime import datetime
from base64 import b64encode
from logservice.logservice import LogService
# from opcua.common import xmlparser

import sys

PLUGIN_VER = "1.0.2"
logger = LogService.getLogger(__name__)

if sys.version_info.major > 2:
    unicode = str


class SubVariableHandler(object):
    def __init__(self, adapter, plugin_name):
        self.adapter = adapter
        self.plugin_name = plugin_name

    def datachange_notification(self, node, val, data):
        json_in = {
            'variable': node.get_display_name().Text,
            'action': 'write',
            'data': val,
        }
        self.adapter.plugin_setvar(self.plugin_name, json_in)


class make_rpc(object):
    def __init__(self, adapter, name, plugin_id):
        self.adapter = adapter
        self.func_name = name
        self.plugin_id = plugin_id

    @uamethod
    def rpc_func(self, *args):
        logger.debug('rpc is called:%s %s', self.func_name, args[1:])
        if len(args) > 1:
            str_args = []
            for i in range(1, len(args)):
                if isinstance(args[i], bytes):
                    base64_bytes = b64encode(args[i])
                    base64_string = base64_bytes.decode('utf-8')
                    str_args.append(base64_string)
                else:
                    str_args.append(args[i])
            #json_in = {'method':self.func_name,'data':args[1:]}
            json_in = {'method': self.func_name, 'data': str_args}
        else:
            json_in = {'method': self.func_name}
        logger.info('### json_in:%s', json_in)
        try:
            retcode, json_out = self.adapter.plugin_call(
                self.plugin_id, json_in)
            logger.debug('out:%s', json_out['data'])
            if retcode == 0:
                # return json_out['data'] #json_out
                return str(json_out['code']), json_out['data']  # json_out
        except Exception as e:
            logger.exception('exception info:%s', e)


class NodeData(object):
    def __init__(self):
        self.name = None
        self.type = None
        self.init_value = None
        self.writable = False
        self.rpc_name = None
        self.value = None
        self.refs = None
        self.input = []
        self.output = []
        self.historizing = None


class JsonImporter(object):

    def __init__(self, server, adapter, plugin_id):
        self.parser = None
        self.server = server
        self.adapter = adapter
        self.namespaces = {}
        self.aliases = {}
        self.plugin_id = plugin_id
        # plugin_call_init()
        self.variable_sub = server.create_subscription(
            500, SubVariableHandler(self.adapter, self.plugin_id))

    def _map_namespaces(self, namespaces_uris):
        """
        creates a mapping between the namespaces in the json file and in the server.
        if not present the namespace is registered.
        """
        namespaces = {}
        for ns_index, ns_uri in enumerate(namespaces_uris):
            ns_server_index = self.server.register_namespace(ns_uri)
            namespaces[ns_index + 1] = ns_server_index
        return namespaces

    def _map_aliases(self, aliases):
        """
        maps the import aliases to the correct namespaces
        """
        aliases_mapped = {}
        for alias, node_id in aliases.items():
            aliases_mapped[alias] = self._migrate_ns(self.to_nodeid(node_id))
        return aliases_mapped

    def _set_attr(self, key, val, obj):
        if key == "name":
            obj.name = val
        elif key == "type":
            obj.type = val
        elif key == "init_value":
            obj.init_value = val
        elif key == "writable":
            if val == "yes":
                obj.writable = True
            else:
                obj.writable = False
        elif key == "rpc_name":
            obj.rpc_name = val
        elif key == "value":
            obj.value = val
        elif key == "input":
            obj.input = val
        elif key == "output":
            obj.output = val
        elif key == "historizing":
            obj.historizing = val
        elif key == "refs":
            obj.refs = val
        else:
            logger.warns("Attribute not implemented: %s:%s", key, val)

    def parse_method(self, parent, idx, method):
        node = NodeData()
        for key, val in method.items():
            self._set_attr(key, val, node)
        input_args = []
        output_args = []
        for i in range(len(node.input)):
            if 'type' in node.input[i]:
                argu = ua.Argument()
                #argu.DataType = getattr(ua.VariantType, node.input[i]['type']).value
                argu.DataType = ua.NodeId(
                    getattr(
                        ua.VariantType,
                        node.input[i]['type']).value)
                if 'name' in node.input[i]:
                    argu.Name = node.input[i]['name']
                logger.info("argu name:%s", argu.Name)
                input_args.append(argu)
        for i in range(len(node.output)):
            if 'type' in node.output[i]:
                argu = ua.Argument()
                #argu.DataType = getattr(ua.VariantType, node.input[i]['type']).value
                argu.DataType = ua.NodeId(
                    getattr(
                        ua.VariantType,
                        node.output[i]['type']).value)
                if 'name' in node.output[i]:
                    argu.Name = node.output[i]['name']
                logger.info('output arg:%s', argu)
                output_args.append(argu)
            else:
                output_args.append(
                    getattr(
                        ua.VariantType,
                        node.output[i]).value)

        rpc = make_rpc(self.adapter, node.rpc_name, self.plugin_id)
        parent.add_method(
            idx,
            node.rpc_name,
            rpc.rpc_func,
            input_args,
            output_args)

    def _parse_varianttype(self, type):
        if type == None:
            return ua.VariantType.Null
        elif type == 'Boolean':
            return ua.VariantType.Boolean
        elif type == 'Double':
            return ua.VariantType.Double
        elif type == 'Int64':
            return ua.VariantType.Int64
        elif type == 'String':
            return ua.VariantType.String
        elif type == 'ByteString':
            return ua.VariantType.ByteString
        elif type == 'DateTime':
            return ua.VariantType.DateTime
        elif type == 'Guid':
            return ua.VariantType.Guid
        else:
            return ua.VariantType.Null

    def _parse_datatype(self, type):
        if type == None:
            return None
        return ua.NodeId(getattr(ua.ObjectIds, self._parse_varianttype(type).name))

    def parse_property(self, parent, idx, prop):
        node = NodeData()
        for key, val in prop.items():
            self._set_attr(key, val, node)

        parent.add_property(idx, node.name, str(node.value), datatype=self._parse_datatype(node.type))

    def parse_variable(self, parent, idx, var):
        node = NodeData()
        for key, val in var.items():
            self._set_attr(key, val, node)

        newvar = parent.add_variable(idx, node.name, node.init_value, datatype=self._parse_datatype(node.type))
        newvar.set_writable(node.writable)
        if node.writable:
            self.variable_sub.subscribe_data_change(newvar)

        if node.historizing is not None:
            self.server.historize_node_data_change(newvar, timedelta(
                node.historizing['period'] / 24), node.historizing['count'])

    def parse_object_children(self, parent, idx, object):
        if 'variables' in object:
            for i in range(len(object['variables'])):
                self.parse_variable(parent, idx, object['variables'][i])
        if 'properties' in object:
            for i in range(len(object['properties'])):
                self.parse_property(parent, idx, object['properties'][i])
        if 'methods' in object:
            for i in range(len(object['methods'])):
                self.parse_method(parent, idx, object['methods'][i])
        if 'objects' in object:
            for i in range(len(object['objects'])):
                self.parse_object(parent, idx, object['objects'][i])

    def parse_object(self, parent, idx, object):
        if parent is None:
            newobject = self.server.nodes.objects.add_object(
                idx, object['name'])
        else:
            newobject = parent.add_object(idx, object['name'])

        self.parse_object_children(newobject, idx, object)

    def parse_folder(self, parent, idx, folder):
        if parent is None:
            newfolder = self.server.nodes.objects.add_folder(
                idx, folder['name'])
        else:
            newfolder = parent.add_folder(idx, folder['name'])

        if 'folders' in folder:
            for i in range(len(folder['folders'])):
                self.parse_folder(newfolder, idx, folder['folders'][i])
        if 'properties' in folder:
            for i in range(len(folder['properties'])):
                self.parse_property(newfolder, idx, folder['properties'][i])
        if 'objects' in folder:
            for i in range(len(folder['objects'])):
                self.parse_object(newfolder, idx, folder['objects'][i])
        if 'methods' in folder:
            for i in range(len(folder['methods'])):
                self.parse_method(newfolder, idx, folder['methods'][i])

        all_object_dicts = {}
        all_object_types = self.server.nodes.base_object_type.get_children()
        for t in all_object_types:
            all_object_dicts[t.get_display_name().to_string()] = t

        for object_type_name, object_type in all_object_dicts.items():
            # object_type_name = type.get_display_name().to_string()
            if object_type_name in folder:
                for i in range(len(folder[object_type_name])):
                    newobject = newfolder.add_object(
                        idx, folder[object_type_name][i]['name'], object_type)
                    # type
                    for node in newobject.get_children():
                        result = node.get_attribute(
                            ua.AttributeIds.Historizing)
                        if result.Value.Value is True:
                            parent_node = object_type.get_child(
                                node.get_browse_name().to_string())
                            period = self.server.iserver.history_manager.storage._datachanges_period[
                                parent_node.nodeid]
                            self.server.historize_node_data_change(
                                node, period[0], period[1])
                    self.parse_object_children(
                        newobject, idx, folder[object_type_name][i])
        return newfolder

    def parse_custom_type(self, parent, idx, object):
        if parent is None:
            all_object_dicts = {}
            all_object_types = self.server.nodes.base_object_type.get_children()
            for t in all_object_types:
                all_object_dicts[t.get_display_name().to_string()] = t

            if not all_object_dicts.get(object['name'], None):
                newobject = self.server.nodes.base_object_type.add_object_type(
                    0, object['name'])
            else:
                return
        else:
            newobject = parent.add_object(idx, object['name'])

        if 'variables' in object:
            for i in range(len(object['variables'])):
                self.parse_variable(newobject, idx, object['variables'][i])
        if 'properties' in object:
            for i in range(len(object['properties'])):
                self.parse_property(newobject, idx, object['properties'][i])
        if 'methods' in object:
            for i in range(len(object['methods'])):
                self.parse_method(newobject, idx, object['methods'][i])
        if 'objects' in object:
            for i in range(len(object['objects'])):
                self.parse_custom_type(newobject, idx, object['objects'][i])

    def import_json(self, jsonpath):
        """
        import json and return added nodes
        """
        logger.info("Importing json file %s", jsonpath)

        with open(jsonpath, 'r') as file:
            data = json.load(file)
            if 'version' in data:
                if PLUGIN_VER != data['version']:
                    logger.warning(
                        "Plugin Version Not Supported, abort loading.")
                    return
            else:
                logger.warning("No Plugin Version Info, abort loading.")
                return

            if 'user_data' in data and 'opcua' in data['user_data']:
                opcua = data['user_data']['opcua']
            else:
                logger.warning("No OPC-UA data in the file, abort loading.")
                return

            if 'user_data' in data and 'apilist' in data['user_data']:
                apilist = data['user_data']['apilist']
            else:
                logger.warning(
                    "No OPC-UA API list in the file, abort loading.")
                return

            if 'endpoint_path' in opcua:
                self.server.set_endpoint(opcua['endpoint_path'])
            else:
                self.server.set_endpoint(
                    "opc.tcp://0.0.0.0:4840/freeopcua/server/")

            if 'broker_path' in opcua:
                self.server.set_server_name(opcua['broker_path'])
            else:
                self.server.set_server_name("FreeOpcUa Example Server")

            if 'uri_name' in opcua:
                idx = self.server.register_namespace(opcua['uri_name'])
            else:
                raise Exception("No URL in JSON file")

            if 'custom_types' in opcua:
                for i in range(len(opcua['custom_types'])):
                    self.parse_custom_type(None, idx, opcua['custom_types'][i])

            if 'objects' in opcua:
                for i in range(len(opcua['objects'])):
                    self.parse_object(None, idx, opcua['objects'][i])

            if 'folders' in opcua:
                for i in range(len(opcua['folders'])):
                    folder = self.parse_folder(None, idx, opcua['folders'][i])
                    for api in apilist:
                        rpc = make_rpc(
                            self.adapter, api['name'], self.plugin_id)
                        folder.add_method(idx, api['name'], rpc.rpc_func)
