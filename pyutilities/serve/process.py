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


import os
import sys
import time
import datetime
import json
import queue
import threading
import subprocess


class Subprocess(object):
    def __init__(self, name, config, manager):
        super(Subprocess, self).__init__()
        self.name = name
        self.config = config
        self.manager = manager
        self.command = ''
        self.pid = 0
        self.state = 'STOPPED'
        self.start_time = None
        self._process = None
        self._thread = None
        self._auto_restart_thread = None
        self.auto_restart_evt = threading.Event()
        self.auto_restart_count = 0
        self.manual_stop = False
        self.is_manager_process = False

    def status(self):
        if self._process:
            retcode = self._process.poll()
            if retcode is not None:
                self.state = 'STOPPED'
                self.start_time = None
        return self.state

    def stop(self):
        self.manual_stop = True
        if self._process:
            self._process.terminate()
            self.state = 'STOPPED'
            self.start_time = None
        if self._thread:
            self._thread.join()
            self._thread = None
        if self._auto_restart_thread:
            self._auto_restart_thread.join()
            self._auto_restart_thread = None
        self.clear_auto_restart()
        return self.status()

    def kill(self):
        if self._process:
            self._process.kill()
            self.state = 'STOPPED'

    def main(self):
        env_dir = self.manager.options.get_env_dir()
        os.chdir(env_dir)
        cmd = self.config['command'].split()
        self._process = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.state = 'Started'
        self.start_time = datetime.datetime.now()

    def run(self, finish_evt):
        self.main()
        return_code = self._process.wait()
        self._process = None
        self.state = 'STOPPED'
        self.start_time = None
        finish_evt.set()
        self.auto_restart_evt.set()
        print('return_code = ', return_code)

    def _start(self):
        finish_evt = threading.Event()
        self.auto_restart_evt.clear()
        self._thread = threading.Thread(
            target=self.run,
            name=self.name,
            args=(finish_evt,)
        )
        self._thread.setDaemon(True)
        self._thread.start()
        if not finish_evt.wait(1.5):
            return True
        return False

    def start(self):
        self.manual_stop = False
        if self._start():
            self.pre_auto_restart()
            return True
        return False

    def pre_auto_restart(self):
        if not self.config['auto_restart']:
            return

        self._auto_restart_thread = threading.Thread(
            target=self._restart_monitor
        )
        self._auto_restart_thread.setDaemon(True)
        self._auto_restart_thread.start()

    def clear_auto_restart(self):
        self.manual_stop = False
        self.auto_restart_count = 0
        self.auto_restart_evt.clear()

    def _restart_monitor(self):
        while self.auto_restart_count < 10:
            if self.auto_restart_evt.wait():
                if self.manual_stop:
                    break
                self._start()
            self.auto_restart_count += 1


class ManagerSubprocess(Subprocess):

    def setup(self, q):
        self.write_q = q
        self.read_q = queue.Queue()

    def stop(self):
        return False

    def main(self):
        env_dir = self.manager.options.get_env_dir()
        os.chdir(env_dir)
        cmd = [
            'python3.5',
            'pymodules/loader.py',
            'pymodules/' +
            self.config['folder']]
        self._process = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.state = 'Started'
        self.start_time = datetime.datetime.now()

        while True:
            line = self._process.stdout.readline()
            time.sleep(0.1)
            if line:
                line = line.decode()
                print('recv = ', line)
                req = self.check_input(line)
                if req:
                    self.dispatch(req)

    def check_input(self, line):
        request = json.loads(line)
        action = request.get('action', None)
        data = request.get('data', None)

        if (action is not None) and (data is not None):
            return request
        return None
        # try:
        #     request = json.loads(line)
        #     if request.get('action') and request.get('data'):
        #         return request
        # except:
        #     pass
        # return None

    def dispatch(self, req):
        request_id = req['request_id']
        action = req.get('action')
        data = req.get('data')

        mname = action
        method = None
        try:
            method = getattr(self.manager, mname)
        except BaseException:
            pass
        if method:
            try:
                ret = method(*data)
            except BaseException:
                ret = {'Success': False, 'Error': 'Unknown error'}
            res = {
                'request_id': request_id,
                'result': ret
            }
            self.send(res)

    def send(self, data):
        if self._process:
            f = self._process.stdin
            f.write(json.dumps(data).encode())
            f.write('\n'.encode())
            f.flush()
