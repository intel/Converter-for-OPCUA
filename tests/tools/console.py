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
import cmd
import requests
import json
import io

from opcua import Client


def listtree(node, tab=0):
    childs = node.get_children()
    childs.sort(key=lambda x: x.get_node_class().value)

    noline = ''
    if tab > 0:
        print(' ' * 4 * (tab - 1), end=noline)
        print('|---', end=noline)

    print(node.get_display_name().Text)
    for c in childs:
        listtree(c, tab + 1)


class PluginConsoleTool(cmd.Cmd):
    intro = '''
Welcome to the (opcua plugin tool) shell.
Type help or ? to list commands.\n
'''
    prompt = '(opcua plugin tool) > '

    def __init__(self):
        super(PluginConsoleTool, self).__init__()
        self.server_uri = "opc.tcp://localhost:4840"
        self.opcua = None
        self.node = None

    def do_plugin_list(self, arg):
        try:
            code, data = self.node.call_method('2:get_plugin_list')
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

    def do_start_plugin(self, arg):
        args = arg.split()
        if len(args) == 1:
            try:
                code, data = self.node.call_method('2:start_plugin', args[0])
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
            print('Error input. example : start_plugin MqttPlugin')

    def do_stop_plugin(self, arg):
        args = arg.split()
        if len(args) == 1:
            try:
                code, data = self.node.call_method('2:stop_plugin', args[0])
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
            print('Error input. example : stop_plugin MqttPlugin')

    def do_getcfg(self, arg):
        args = arg.split()
        if len(args) == 3:
            dirname = os.path.realpath(args[2])
            if os.path.isdir(dirname):
                try:
                    code, data = self.node.call_method(
                        '2:getcfg', args[0], args[1])
                    if code == '0':
                        result = json.loads(data)
                        if result['Error']:
                            print(result['Error'])
                        else:
                            with open(os.path.join(dirname, result['Success']['filename']), "w") as f:
                                f.write(result['Success']['data'])
                            print(
                                'saved file to %s' %
                                os.path.join(
                                    dirname,
                                    result['Success']['filename']))
                    else:
                        print(code, data)

                except Exception as e:
                    print(repr(e))

            else:
                print(
                    'folder not exist, please enter the correct directory used to store files')
        else:
            print('Error input. example : getcfg mqttplugin json /home/test/')

    def do_setcfg(self, arg):
        args = arg.split()
        if len(args) == 3:
            if os.path.isfile(os.path.realpath(args[2])):
                fp = os.path.realpath(args[2])
                s = ''
                with open(fp, 'r') as f:
                    s = f.read()

                try:
                    code, data = self.node.call_method(
                        '2:setcfg', args[0], args[1], s)
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
            print('Error input. example : setcfg mqttplugin json /home/test/t.json')

    def do_call(self, arg):
        args = arg.split()
        if len(args) > 1:
            plugin_name = args[0:1][0]
            method_name = args[1:2][0]
            params = args[2:]

            if plugin_name == 'manager':
                print("manager plugin not allow call_method in console tools")
                return

            plugin_node = None
            try:
                plugin_node = self.root.get_child(
                    ["0:Objects", "2:" + plugin_name])
            except BaseException:
                print(
                    'Cannot find {0}, please check the plugin is started.'.format(plugin_name))

            if plugin_node:
                methods = plugin_node.get_methods()
                func = None
                for m in methods:
                    if m.get_display_name().Text == method_name:
                        func = m
                if func:
                    try:
                        result = plugin_node.call_method(func, *params)
                        print(result)
                    except BaseException:
                        pass
                else:
                    print('object has not method ({0}).'.format(method_name))
        else:
            print('example : call KvPlugin put key value')

    def do_tree(self, arg):
        args = arg.split()
        if len(args) == 1:
            plugin_name = args[0]
            if plugin_name == 'manager':
                print("manager plugin operation is not supported")
                return

            plugin_node = None
            try:
                plugin_node = self.root.get_child(
                    ["0:Objects", "2:" + plugin_name])
            except BaseException:
                print(
                    'Cannot find {0}, please check the plugin is started.'.format(plugin_name))

            if plugin_node:
                listtree(plugin_node, tab=0)
        else:
            print('example : tree KvPlugin')

    def do_exit(self, arg):
        print('GOOD BAY')
        return True

    def preloop(self):
        self.opcua = Client(self.server_uri)
        try:
            self.opcua.connect()
        except BaseException:
            self.bye('Connect opcua server failed. %s' % self.server_uri)
        self.root = self.opcua.get_root_node()
        try:
            self.node = self.root.get_child(["0:Objects", "2:ManagerPlugin"])
        except BaseException:
            self.bye(
                'Cannot find the ManagerPlugin node, maybe the Manager plugin not started.')

    def postloop(self):
        if self.opcua:
            self.opcua.disconnect()

    def default(self, line):
        print('Unknown command, please try help')

    def bye(self, msg):
        print(msg)
        print('Application exit')
        if self.opcua:
            try:
                self.opcua.disconnect()
            except BaseException:
                pass
        exit(1)


if __name__ == '__main__':
    PluginConsoleTool().cmdloop()
