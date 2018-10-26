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


from socket import *
import sys

sys.path.append("../../../pyutilities/")
from logservice.logservice import LogService

logger = LogService.getLogger(__name__)


HOST = '127.0.0.1'
PORT = 80
BUFSIZ = 1024
ADDR = (HOST, PORT)
sock = socket(AF_INET, SOCK_STREAM)
sock.bind(ADDR)
sock.listen(5)

STOP_CHAT = False

logger.debug(sys.getdefaultencoding())

while not STOP_CHAT:
    #print(u"wating incoming connections，listening port: %d" % (PORT))
    logger.debug("wating incoming connections，listening port: %d" % (PORT))
    tcpClientSock, addr = sock.accept()
    #print('accept connection from: %s ')
    logger.debug('accept connection from: %s:%s' % (HOST, PORT))
    while True:
        try:
            data = tcpClientSock.recv(BUFSIZ)
        except BaseException:
            logger.exception('')
            tcpClientSock.close()
            break
        if not data:
            break
        s = 'return data-%s from %s' % (data, addr[0])
        logger.debug(s)
        tcpClientSock.send(s.encode('ascii'))  # .encode('utf8'))
        logger.debug(data.decode('utf8'))
        STOP_CHAT = (data.decode('utf8').upper() == "Q")
        if STOP_CHAT:
            break
tcpClientSock.close()
sock.close()
