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
import re
from enum import Enum
from six import string_types

PARSE_TYPE = {
    'String': str,
    'string': str,
    'str': str,
    'int': int,
    'Int': int,
    'Integer': int,
    'Long': int,
    'long': int,
    'Float': float,
    'float': float,
    'Double': float,
    'double': float,
    'Bool': bool,
    'bool': bool,
}


class NodeType(Enum):
    UnKnown = 0
    Folder = 1
    Variable = 2
    Property = 3
    Method = 4
    Object = 5
    CustomObj = 6


class Method(object):
    def __init__(self, name, inputs, outputs):
        self.name = name
        self.input_params = []
        self.required = 0

        for i, node in enumerate(inputs):
            default = None
            has_default = False
            if isinstance(node, string_types):
                node_type = node
            elif isinstance(node, dict):
                node_type = node.get('type', 'String')
                if 'default' in node:
                    default = node.get('default', None)
                    has_default = True
            if has_default is not True:
                self.required += 1

            node_type = PARSE_TYPE.get(node_type)
            input_param = {
                'type': node_type,
                'has_default': has_default,
                'default': default}
            self.input_params.append(input_param)

    def check_inputs(self, input_list):
        args = []
        if not input_list:
            if self.required > 0:
                return False, [], '(%s) method expect at least (%s) positional arguments, but (%s) were given' % (
                    self.name, self.required, 0)
        else:
            if len(input_list) < self.required:
                return False, [], '(%s) method expect at least (%s) positional arguments, but (%s) were given' % (
                    self.name, self.required, len(input_list))
            elif len(input_list) > len(self.input_params):
                return False, [], '(%s) method expect most (%s) positional arguments, but (%s) were given' % (
                    self.name, len(self.input_params), len(input_list))
            else:
                i = 0
                flag = True
                while i < len(input_list) and flag:
                    new_input = input_list[i]
                    if new_input is None:
                        if self.input_params[i]['has_default'] is True:
                            new_input = self.input_params[i]['default']
                        else:
                            return False, None, '(%s) method the idx (%s) parameter not allow empty' % (
                                self.name, i + 1)

                    if not isinstance(new_input, self.input_params[i]['type']):
                        try:
                            new_input = self.input_params[i]['type'](new_input)
                        except BaseException:
                            return False, None, '(%s) method the idx (%s) parameter type conversion error, expect (%s)' % (
                                self.name, i + 1, re.match(r"^[<]class\s'(\S+)'[>]$", str(self.input_params[i]['type'])).group(1))
                    i += 1
                    args.append(new_input)

        return True, args, 'OK'


class Node(object):
    def __init__(self, name, object=None, type=NodeType.UnKnown, value=None):
        self.name = name
        self.type = type
        self.value = value
        self.parent = None
        self.pair_friend = None
        self.children = []
        if object is not None:
            for child in object.get_children():
                self.add_child(child)

    def get_parent(self):
        return self.parent

    def add_child(self, node):
        for child in self.children:
            if child.name == node.name:
                return child
        node.parent = self
        self.children.append(node)
        return node

    def get_children(self):
        return self.children

    def get_child(self, name):
        for child in self.children:
            if child.name == name:
                return child
        return None

    def add_pair_friend(self, node):
        self.pair_friend = node

    def get_pair_friend(self):
        return self.pair_friend


class BasePluginEntity(object):
    def __init__(self, file_name):
        self.file_name = file_name
        self.root_node = None
        self.custom_obj_types = []
        self.custom_nodes = []
        self.plugin_name = None
        self.topic_name = None
        self.data = None
        self.node_methods = {}
        self.api_methods = {}
        self.loads(file_name)

    def add_method(self, func_name, inputs, outputs):
        self.node_methods[func_name] = Method(func_name, inputs, outputs)

    def add_api_method(self, func_name, inputs, outputs):
        self.api_methods[func_name] = Method(func_name, inputs, outputs)

    def parse_node(self, parent, node_data):
        if 'methods' in node_data:
            for m in node_data['methods']:
                ins = []
                if 'input' in m:
                    ins = m['input']
                self.add_method(m['name'], ins, m['output'])
        if 'folders' in node_data:
            for folder in node_data['folders']:
                node = parent.add_child(
                    Node(folder['name'], type=NodeType.Folder))
                self.parse_node(node, folder)
        if 'objects' in node_data:
            for object in node_data['objects']:
                node = parent.add_child(
                    Node(object['name'], type=NodeType.Object))
                self.parse_node(node, object)
        if 'variables' in node_data:
            for var in node_data['variables']:
                parent.add_child(Node(var['name'], type=NodeType.Variable))
        if 'properties' in node_data:
            for var in node_data['properties']:
                val = None
                if 'value' in var:
                    val = var['value']
                node = Node(var['name'], type=NodeType.Property, value=val)
                if 'refs' in var:
                    friend = parent.get_child(var['refs'])
                    node.add_pair_friend(friend)
                parent.add_child(node)
        for node in self.custom_obj_types:
            if node.name in node_data:
                for c_node in node_data[node.name]:
                    new_node = Node(
                        c_node['name'], node, type=NodeType.CustomObj)
                    self.parse_node(new_node, c_node)
                    self.custom_nodes.append(new_node)
                    parent.add_child(new_node)

    def list_node(self, node):
        children = node.get_children()
        for child in children:
            self.list_node(child)

    def _get_node_by_val(self, node, value):
        if node.value == value:
            return node
        children = node.get_children()
        for child in children:
            node = self._get_node_by_val(child, value)
            if node is not None:
                return node
        return None

    def _get_node_by_type(self, node, type):
        if node.type == type:
            return node
        children = node.get_children()
        for child in children:
            node = self._get_node_by_type(child, type)
            if node is not None:
                return ret
        return None

    def get_children_by_type(self, parent, type):
        nodes = []
        children = parent.get_children()
        for child in children:
            if child.type == type:
                nodes.append(child)
        return nodes

    def get_custom_nodes(self):
        return self.custom_nodes

    def get_property(self, node, name):
        children = node.get_children()
        for child in children:
            if child.type == NodeType.Property:
                if child.name == name:
                    return child
        return None

    def get_node_by_val(self, value, parent=None):
        if not parent:
            parent = self.root_node
        return self._get_node_by_val(parent, value)

    def get_methods(self):
        return dict(self.node_methods, **self.api_methods)

    def parse_api(self):
        apilist = self.data['user_data']['apilist']
        for api in apilist:
            ins = []
            if 'input' in api:
                ins = api['input']
            self.add_api_method(api['name'], ins, api['output'])

    def loads(self, json_file):
        file = open(json_file, 'r')
        json_data = file.read()
        file.close()
        self.data = json.loads(json_data)
        self.topic_name = self.data['user_data']['topic']
        self.plugin_name = self.topic_name.split('/')[1]
        self.parse_api()
        opcua = self.data['user_data']['opcua']
        if 'custom_types' in opcua:
            for custom_type in opcua['custom_types']:
                node = Node(custom_type['name'])
                self.parse_node(node, custom_type)
                self.custom_obj_types.append(node)
        if 'folders' in opcua:
            folder0 = opcua['folders'][0]
            self.root_node = Node(folder0['name'])
            self.parse_node(self.root_node, folder0)
            # self.list_node(self.root_node)
