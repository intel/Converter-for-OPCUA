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
import queue
import sys
from optparse import OptionParser

sys.path.append('../../')

from pyutilities.serve.options import Options
from pyutilities.serve.daemon import daemonize
from pyutilities.serve.core import PluginManager

VERSION = 1.0


def main():
    parser = OptionParser(usage='usage: %prog [options] ...',
                          version='%%prog %s' % VERSION)

    if os.name == 'posix':
        parser.add_option('-d', '--daemonize', action='store_true',
                          dest='daemonize',
                          help='run in the background as a daemon')
        parser.add_option('--pidfile', action='store',
                          dest='pidfile',
                          help='when daemonizing, file to which to write pid')

    options, args = parser.parse_args()

    if options.daemonize and options.autoreload:
        parser.error('the --auto-reload option cannot be used with '
                     '--daemonize')

    if parser.has_option('pidfile') and options.pidfile:
        options.pidfile = os.path.abspath(options.pidfile)

    q = queue.Queue()

    opt = Options('default.conf')
    manager = PluginManager(opt, q)
    manager.run()

    try:
        if options.daemonize:
            daemonize(pidfile=options.pidfile, progname='opcua_plugin')

    except OSError as e:
        print("%s: %s" % (e.__class__.__name__, e), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
