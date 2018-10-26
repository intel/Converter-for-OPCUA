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


class ReturnCodes(object):
    Good = 0

    # for SCPI Serial Plugin
    SCPI_SerialOpenFail = 0x00002000
    SCPI_SerialCloseFail = 0x00002001
    SCPI_SerialNotOpen = 0x00002002
    SCPI_SerialNoResponse = 0x00002003
    SCPI_SerialNoInited = 0x00002004
    SCPI_SerialSendFail = 0x00002005
    SCPI_SerialListStateFail = 0x00002006
    SCPI_SerialReadStateException = 0x00002007

    # for SCPI Tcp Plugin
    SCPI_TcpOpenException = 0x00003000
    SCPI_TcpCloseFail = 0x00003001
    SCPI_TcpCloseException = 0x00003002
    SCPI_TcpNoInited = 0x00003003
    SCPI_TcpSendException = 0x00003004
    SCPI_TcpListStateFail = 0x00003005
    SCPI_TcpReadStateException = 0x00003006

    # for Plugin Global
    PLUGIN_ParamError = 0x00004000
    PLUGIN_RpcError = 0x00004001
    # for user definition
