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

import glob
import os
import signal
import datetime
import time
import threading

from pyutilities.serve.process import Subprocess, ManagerSubprocess


class PluginManager(object):

    def __init__(self, options, q):
        self.Q = q
        self.options = options
        self.loader_py = options.get_loader_py()
        self.processes = {}
        self.manager_process = None
        self.stop_sig = threading.Event()

    def stop(self, signum, frame):
        self.stop_sig.set()

    def create_process(self, name, opt):
        if opt.get('manager', False):
            process = ManagerSubprocess(name, opt, self)
            self.manager_process = process
            self.manager_process.setup(self.Q)
        else:
            process = Subprocess(name, opt, self)
        self.processes[name] = process

    def run(self):

        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

        for name, opt in self.options.plugin_options.items():
            self.create_process(name, opt)

        for p in self.processes.values():
            if p.config['auto_start']:
                p.start()

        signal.pause()

    def start_plugin(self, name):
        result = {'Success': False, 'Error': False}
        process = self.processes.get(name, None)
        if process:
            if process.state == 'STOPPED':
                if process.start():
                    result['Success'] = 'OK'
                else:
                    result['Error'] = '{0} plugin maybe run error'.format(name)
            else:
                result['Error'] = '{0} plugin is started'.format(name)
        else:
            result['Error'] = '{0} plugin not found'.format(name)
        return result

    def stop_plugin(self, name):
        result = {'Success': False, 'Error': False}
        process = self.processes.get(name, None)
        if process:
            if not process.is_manager_process:
                process.stop()
                result['Success'] = 'OK'
            else:
                result['Error'] = 'Manager plugin cannot be stopped'
        else:
            result['Error'] = '{0} plugin not found'.format(name)
        return result

    def get_plugin_list(self):
        print('core get_plugin_list')
        result = {'Success': False, 'Error': False}

        ps = []
        for key, p in self.processes.items():
            obj = {
                'name': key,
                'status': p.status(),
            }
            if obj['status'] == 'Started':
                obj['start_time'] = format_humer_time(p.start_time)

            ps.append(obj)
        result['Success'] = ps
        return result

    def getcfg(self, name, cfg_type):
        result = {'Success': False, 'Error': False}
        process = self.processes.get(name, None)
        if process:
            plugin_home = os.path.join(
                self.options.get_plugin_folder(),
                process.config['folder'])
            if cfg_type.upper() == 'JSON':
                files = glob.glob(os.path.join(plugin_home, '*.json'))
            elif cfg_type.upper() == 'CONF':
                files = glob.glob(os.path.join(plugin_home, '*.conf'))

            if len(files) == 1:
                s = ''
                with open(files[0], 'r') as f:
                    s = f.read()
                result['Success'] = {
                    'filename': os.path.basename(files[0]),
                    'data': s
                }
            elif len(files) < 1:
                result['Error'] = 'plugin home config file not found.'
            else:
                result['Error'] = 'plugin home has more than one file.'
        else:
            result['Error'] = '{0} plugin not found'.format(name)
        return result

    def setcfg(self, name, cfg_type, s):
        result = {'Success': False, 'Error': False}
        process = self.processes.get(name, None)
        if process:
            if process.state == 'STOPPED':
                plugin_home = os.path.join(
                    self.options.get_plugin_folder(),
                    process.config['folder'])
                if cfg_type.upper() == 'JSON':
                    files = glob.glob(os.path.join(plugin_home, '*.json'))
                elif cfg_type.upper() == 'CONF':
                    files = glob.glob(os.path.join(plugin_home, '*.conf'))

                if len(files) == 1:
                    with open(files[0], 'w') as f:
                        f.write(s)
                    result['Success'] = 'OK'
                elif len(files) < 1:
                    result['Error'] = 'plugin home config file not found.'
                else:
                    result['Error'] = 'plugin home has more than one file.'
            else:
                result['Error'] = 'plugin not stoped, please stop the plugin first.'
        return result


def format_humer_time(t):
    if not t:
        return '0s'
    now = datetime.datetime.now()
    minute = 60
    hour = 60 * minute
    delta = (now - t)
    seconds = delta.seconds

    d = delta.days
    h = seconds // hour
    m = (seconds - (h * hour)) // minute
    s = seconds % 60

    return '{0}day {1}hour {2}min {3}s'.format(d, h, m, s)
