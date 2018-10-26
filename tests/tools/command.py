# !/usr/bin/env python3.5
# -*- coding: utf-8 -*-
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

import os
import sys
import cmd
import re
import json

from opcua import Client, ua
from opcua.common.ua_utils import val_to_string


def listtree(node, tab=0, level=2, out=sys.stdout):
    if tab > level:
        return
    childs = node.get_children()
    childs.sort(key=lambda x: x.get_node_class().value)

    if tab > 0:
        out.write(' ' * 4 * (tab - 1))
        out.write('|---')

    out.write('{0}  ({1})'.format(node.get_display_name().Text, node.nodeid.to_string()))
    out.write('\n')
    for c in childs:
        listtree(c, tab + 1, level, out=out)


def data_type_to_string(dtype):
    if dtype.Identifier in ua.ObjectIdNames:
        string = ua.ObjectIdNames[dtype.Identifier]
    else:
        string = dtype.to_string()
    return string


def attr_to_enum(attr):
    attr_name = attr.name
    if attr_name.startswith("User"):
        attr_name = attr_name[4:]
    return getattr(ua, attr_name)


def enum_to_string(attr, val):
    attr_enum = attr_to_enum(attr)
    string = ", ".join([e.name for e in attr_enum.parse_bitfield(val)])
    return string


def show_attrs(attrs):
    for attr, dv in attrs:
        if attr == ua.AttributeIds.Value:
            show_value_attr(attr, dv)
        else:
            show_attr(attr, dv)


def show_attr(attr, dv):
    if attr == ua.AttributeIds.DataType:
        string = data_type_to_string(dv.Value.Value)
    elif attr in (ua.AttributeIds.AccessLevel,
                  ua.AttributeIds.UserAccessLevel,
                  ua.AttributeIds.WriteMask,
                  ua.AttributeIds.UserWriteMask,
                  ua.AttributeIds.EventNotifier):
        string = enum_to_string(attr, dv.Value.Value)
    else:
        string = val_to_string(dv.Value.Value)
    print(attr.name, ':', string)


def show_value_attr(attr, dv):
    print('Value', ':', dv.Value.Value)
    print('Server Timestamp', ':', val_to_string(dv.ServerTimestamp))
    print('Source Timestamp', ':', val_to_string(dv.SourceTimestamp))


class PluginConsoleTool(cmd.Cmd):
    intro = '''
Welcome to the (opcua plugin tool) shell.
Type help or ? to list commands.\n
'''
    prompt = '(Disconnected) > '

    def __init__(self):
        super(PluginConsoleTool, self).__init__()
        self.server_uri = None
        self.opcua = None
        self.root = None
        self.node = None

    def disconnect(self):
        if self.opcua:
            try:
                self.opcua.disconnect()
            except:
                pass
        self.server_uri = None
        self.opcua = None
        self.root = None
        self.__class__.prompt = '(Disconnected) > '

    def check_connect(self):
        connected = False
        if self.opcua:
            try:
                self.opcua.send_hello()
                connected = True
            except:
                pass
        if not connected:
            print("Disconnected, please connect server first")
        return connected

    def goto(self, node):
        self.node = node
        self.__class__.prompt = '({0}  ({1})) > '.format(node.get_display_name().Text, node.nodeid.to_string())

    def do_goto(self, arg):
        args = arg.split()
        if len(args) == 1:
            if self.check_connect():
                nodeid = args[0]
                if nodeid == 'root':
                    node = self.root
                else:
                    try:
                        node = self.opcua.get_node(nodeid=nodeid)
                        node.get_display_name()
                    except:
                        print('Can not found this node ({0})'.format(nodeid))
                        node = None

                if node:
                    self.goto(node)
        else:
            print('example : goto i=10 | goto root')

    def help_goto(self):
        print('Locate to a node, the prompt will display this node name. example (Root  (i=84)) > ')
        print('usage: goto {nodeid} | goto root')
        print('example: goto i=84 | goto ns=2;i=100 | goto root')

    def do_connect(self, arg):
        args = arg.split()
        if len(args) == 1:
            uri = args[0]
            self.server_uri = uri

            try:
                self.opcua = Client(self.server_uri)
                self.opcua.connect()
                print('Connected Success')
            except:
                print('Connect failed')
                self.opcua = None

            if self.opcua:
                self.root = self.opcua.get_root_node()
                self.goto(self.root)
        else:
            print('example : connect opc.tcp://localhost:4840')

    def do_disconnect(self, arg):
        self.disconnect()
        print('Disconnected')

    def check_tree_arg(self, arg):
        args = arg.split()
        verified = False
        level = 1
        if len(args) <= 1:
            if not self.check_connect():
                return

            if len(args) == 1:
                a = args[0]

                try:
                    level = int(a)
                    verified = True
                except:
                    m = re.match(r'^max-depth=(\d+)$', a)
                    if m:
                        level = int(m.group(1))
                        verified = True
            else:
                level = 2
                verified = True
        return verified, level

    def do_tree(self, arg):
        verified, level = self.check_tree_arg(arg)
        if verified:
            listtree(self.node, tab=0, level=level)
        else:
            print('example : tree | tree 2 | tree max-depth=2')

    def do_dump_tree(self, arg):
        verified, level = self.check_tree_arg(arg)
        if verified:
            cwd = os.getcwd()
            dest_fp = os.path.join(cwd, '{}.tree'.format(self.node.get_display_name().Text))
            with open(dest_fp, 'w') as df:
                listtree(self.node, tab=0, level=level, out=df)
                print('saved file to {}'.format(dest_fp))

        else:
            print('example : dump_tree | dump_tree 2 | dump_tree max-depth=2')

    def do_attrs(self, arg):
        args = arg.split()
        if len(args) == 0:
            if not self.check_connect():
                return

            attrs = self.get_all_attrs()
            show_attrs(attrs)
        else:
            print('example : attrs')

    def do_set_value(self, arg):
        args = arg.split()
        if len(args) == 1:
            value = args[0]
            if not self.check_connect():
                return

            try:
                self.node.set_value(value)
                print('set value Success')
            except Exception as e:
                print('set value Error. please check current node datatype')

        else:
            print('example : attrs')

    def do_methods(self, arg):
        args = arg.split()
        if len(args) == 0:
            if not self.check_connect():
                return

            method_list = self.node.get_methods()
            for m in method_list:
                print(m.get_display_name().Text)
        else:
            print('example : methods')

    def do_call(self, arg):
        args = arg.split()
        if len(args) >= 1:
            if not self.check_connect():
                return

            method_name = args[0:1][0]
            params = args[1:]

            methods = self.node.get_methods()
            func = None
            for m in methods:
                if m.get_display_name().Text == method_name:
                    func = m
            if func:
                try:
                    result = self.node.call_method(func, *params)
                    print(result)
                except Exception as e:
                    print('Call method failed')
                    print(e)
            else:
                print('node has not method ({0}).'.format(method_name))
        else:
            print('example : call {method_name} [param1] [param2] ...')

    def do_setcfg(self, arg):
        args = arg.split()
        if len(args) == 4:
            if not self.check_connect():
                return

            if self.node != self.opcua.get_root_node():
                print('please goto root first and then execute this method.')
                return

            manage_plugin_name = args[0]
            plugin_name = args[1]
            ftype = args[2]
            fp = args[3]
            manage_plugin_node = None

            objects = self.opcua.get_objects_node().get_children()
            for n in objects:
                if n.get_display_name().to_string() == manage_plugin_name:
                    manage_plugin_node = n
                    break

            if not manage_plugin_node:
                print('Can not find ({0}) manage plugin node'.format(manage_plugin_name))
                return

            if os.path.isfile(os.path.realpath(fp)):
                s = ''
                with open(fp, 'r') as f:
                    s = f.read()

                try:
                    code, data = manage_plugin_node.call_method('2:setcfg', plugin_name, ftype, s)
                    if code == '0':
                        result = json.loads(data)
                        if result['Error']:
                            print(result['Error'])
                        else:
                            print(result['Success'])
                    else:
                        print(code, data)
                except Exception as e:
                    print(repr(e))

            else:
                print('source file not exist, please enter the correct path to upload')
        else:
            self.help_setcfg()


    def help_setcfg(self):
        print('Special method to upload plugin configuration files')
        print('please goto root first and then execute this method. Otherwise it will fail.')
        print('usage: ')
        print('1. goto root')
        print('2. setcfg {manager plugin name} {plugin name} {json | conf} {file path}')
        print('example: setcfg manage_plugin_127.0.0.1_host MqttPlugin json /home/root/plugin.json')


    def do_getcfg(self, arg):
        args = arg.split()
        if len(args) == 4:
            if not self.check_connect():
                return

            if self.node != self.opcua.get_root_node():
                print('please goto root first and then execute this method.')
                return

            manage_plugin_name = args[0]
            plugin_name = args[1]
            ftype = args[2]
            dirname = args[3]
            manage_plugin_node = None

            objects = self.opcua.get_objects_node().get_children()
            for n in objects:
                if n.get_display_name().to_string() == manage_plugin_name:
                    manage_plugin_node = n
                    break

            if not manage_plugin_node:
                print('Can not find ({0}) manage plugin node'.format(manage_plugin_name))
                return

            if os.path.isdir(dirname):
                try:
                    code, data = manage_plugin_node.call_method('2:getcfg', plugin_name, ftype)
                    if code == '0':
                        result = json.loads(data)
                        if result['Error']:
                            print(result['Error'])
                        else:
                            with open(os.path.join(dirname, result['Success']['filename']), "w") as f:
                                f.write(result['Success']['data'])

                            print('saved file to %s' % os.path.join(
                                dirname,
                                result['Success']['filename']
                            ))
                    else:
                        print(code, data)
                except Exception as e:
                    print(repr(e))
            else:
                print('folder not exist, please enter the correct directory used to store files')
        else:
            self.help_getcfg()

    def help_getcfg(self):
        print('Special method to download plugin configuration files')
        print('please goto root first and then execute this method. Otherwise it will fail.')
        print('usage: ')
        print('1. goto root')
        print('2. getcfg {manager plugin name} {plugin name} {json | conf} {dest folder path}')
        print('example: getcfg manage_plugin_127.0.0.1_host MqttPlugin json /home/root/')

    def do_exit(self, arg):
        print('Good Bye')
        return True

    def postloop(self):
        self.disconnect()

    def default(self, line):
        print('Unknown command, please try help')

    def bye(self, msg):
        print(msg)
        print('Application exit')
        self.disconnect()
        exit(1)

    def get_all_attrs(self):
        attrs = [attr for attr in ua.AttributeIds]
        dvs = self.node.get_attributes(attrs)
        res = []
        for idx, dv in enumerate(dvs):
            if dv.StatusCode.is_good():
                res.append((attrs[idx], dv))
        res.sort(key=lambda x: x[0].name)
        return res


if __name__ == '__main__':
    PluginConsoleTool().cmdloop()
