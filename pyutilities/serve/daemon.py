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


import atexit
import errno
import os
import signal
import sys


def daemonize(pidfile=None, progname=None, stdin='/dev/null',
              stdout='/dev/null', stderr='/dev/null', umask=0o022):
    """Fork a daemon process."""
    if pidfile:
        # Check whether the pid file already exists and refers to a still
        # process running
        pidfile = os.path.abspath(pidfile)
        if os.path.exists(pidfile):
            with open(pidfile) as fileobj:
                try:
                    pid = int(fileobj.read())
                except ValueError:
                    sys.exit('Invalid pid in file %s\nPlease remove it to '
                             'proceed' % pidfile)

            try:  # signal the process to see if it is still running
                os.kill(pid, 0)
                if not progname:
                    progname = os.path.basename(sys.argv[0])
                sys.exit('%s is already running with pid %s' % (progname, pid))
            except OSError as e:
                if e.errno != errno.ESRCH:
                    raise

        # The pid file must be writable
        try:
            fileobj = open(pidfile, 'a+')
            fileobj.close()
        except IOError as e:
            sys.exit('Error writing to pid file')

    # Perform first fork
    pid = os.fork()
    if pid > 0:
        sys.exit(0)  # exit first parent

    # Decouple from parent environment
    os.chdir('/')
    os.umask(umask)
    os.setsid()

    # Perform second fork
    pid = os.fork()
    if pid > 0:
        sys.exit(0)  # exit second parent

    # The process is now daemonized, redirect standard file descriptors
    for stream in sys.stdout, sys.stderr:
        stream.flush()
    stdin = open(stdin, 'r')
    stdout = open(stdout, 'ab+')
    stderr = open(stderr, 'ab+', 0)
    os.dup2(stdin.fileno(), sys.stdin.fileno())
    os.dup2(stdout.fileno(), sys.stdout.fileno())
    os.dup2(stderr.fileno(), sys.stderr.fileno())

    if pidfile:
        # Register signal handlers to ensure atexit hooks are called on exit
        for signum in [signal.SIGTERM, signal.SIGHUP]:
            signal.signal(signum, handle_signal)

        # Create/update the pid file, and register a hook to remove it when the
        # process exits
        def remove_pidfile():
            if os.path.exists(pidfile):
                os.remove(pidfile)
        atexit.register(remove_pidfile)
        with open(pidfile, 'w') as fileobj:
            fileobj.write(str(os.getpid()))


def handle_signal(signum, frame):
    """Handle signals sent to the daemonized process."""
    sys.exit()
