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
import threading
import time
import json
from enum import Enum
from client import BasePluginClient
from entity import BasePluginEntity
from config import BasePluginConfig
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.exceptions import ConnectionException
from logservice.logservice import LogService
from ret_codes import ReturnCodes

logger = LogService.getLogger(__name__)


class MBDataType(Enum):
    COILS = 0
    DISCRETE_INPUTS = 1
    HOLDING_REGS = 2
    INPUT_REGS = 3


class ModbusPluginEntity(BasePluginEntity):
    def __init__(self, file_name):
        super(ModbusPluginEntity, self).__init__(file_name)


class ModbusPluginConfig(BasePluginConfig):
    def __init__(self, config_fp):
        super(ModbusPluginConfig, self).__init__(config_fp)


class ModbusPluginClient(BasePluginClient):
    def __init__(self, entity, config):
        super(ModbusPluginClient, self).__init__(entity, config)
        self.modbus_devices = self.entity.get_custom_nodes()
        self.modbus_clients = {}
        self.clients = []
        self.is_stop = False
        self._main = None

    def _start(self):
        for device in self.modbus_devices:
            address = self.entity.get_property(device, 'device address')
            if address is None:
                continue
            uri = address.value
            if uri is None:
                continue

            host = uri.split(':')[0]
            port = uri.split(':')[1]
            self.modbus_clients[uri] = {
                'name': device.name,
                'uri': uri,
                'connected': False,
                'host': host,
                'port': port,
                'node_data': device,
                'predefined': True,
                'client': ModbusClient(host, port)
            }

        for c in self.modbus_clients.values():
            c['client'].close()
            c['connected'] = c['client'].connect()

        self._main = threading.Thread(target=self._plugin_main, args=(None,))
        self._main.setDaemon(True)
        self._main.start()

    def _stop(self):
        self.is_stop = True
        self._main.join()
        self._main = None
        for c in self.modbus_clients.values():
            c['client'].close()
            c['connected'] = False

    def start(self):
        self._start()
        super(ModbusPluginClient, self).start()

    def stop(self):
        self._stop()
        super(ModbusPluginClient, self).stop()

    def restart(self, uri):
        if uri:
            c = self.modbus_clients.get(uri, None)
            if c and (not c['predefined']):
                c['client'].close()
                c['connected'] = c['client'].connect()
        else:
            self._stop()
            self._start()

    def getstate(self, name=None):
        return {
            'code': ReturnCodes.Good,
            'data': json.dumps(self.get_client_state(name))
        }

    def is_client_connected(self, name):
        if name:
            c = self.modbus_clients.get(name, None)
            if c['connected']:
                # c['client'].close()
                c['connected'] = c['client'].connect()
                return c['connected']
        return False

    def get_client_state(self, uri):
        res = []
        client_list = []
        if uri:
            c = self.modbus_clients.get(uri, None)
            if c:
                client_list.append(c)
        else:
            client_list = self.modbus_clients.values()

        for client in client_list:
            if client['connected']:
                client['client'].close()
                client['connected'] = client['client'].connect()
            res.append(json.dumps({
                'name': client['uri'],
                'connected': 'connected' if client['connected'] else 'disconnected',
            }))

        return res

    def refresh(self):
        # TBD
        return {'code': ReturnCodes.PLUGIN_ParamError,
                'data': 'No yet implemented in this Plugin'}

    def plugin_poll(self):
        for device in self.modbus_devices:
            msg = 'online'
            address = self.entity.get_property(device, 'device address')
            if address is None:
                msg = 'offline'
            elif not self.is_client_connected(address.value):
                msg = 'offline'
            self.pub_event(device.name, msg, '')

    def _fetch_client(self, uri):
        if uri in self.modbus_clients:
            return self.modbus_clients[uri]
        return None

    def connect(self, uri):
        ret_code = 1
        result = 'connect failed'

        try:
            host = uri.split(':')[0]
            port = uri.split(':')[1]
        except BaseException:
            return {'code': ReturnCodes.PLUGIN_ParamError,
                    'data': 'modbus-tcp plugin connect parameter error'}

        if uri not in self.modbus_clients:
            client = ModbusClient(host, port)
            self.modbus_clients[uri] = {
                'name': uri,
                'uri': uri,
                'connected': False,
                'host': host,
                'port': port,
                'node_data': None,
                'predefined': False,
                'client': client
            }

        c = self.modbus_clients[uri]
        c['client'].close()
        c['connected'] = c['client'].connect()
        if c['connected']:
            ret_code = ReturnCodes.Good
            result = 'connect success'

        return {'code': ret_code, 'data': result}

    def disconnect(self, uri):
        ret_code = 1
        result = 'device not found'

        client = self._fetch_client(uri)
        if client:
            if client['predefined']:
                result = 'disconnect not allow'
            else:
                client['client'].close()
                client['connected'] = False
                ret_code = ReturnCodes.Good
                result = 'disconnect success'
        return {'code': ret_code, 'data': result}

    def write_coil(self, uri, address, value):
        ret_code = 1
        result = 'device not found'

        client = self._fetch_client(uri)
        if client:
            try:
                rq = client['client'].write_coil(address, value)
                if rq.function_code < 0x80:
                    ret_code = ReturnCodes.Good
                    result = 'OK'
                else:
                    result = 'failed with function_code%s' % rq.function_code
            except ConnectionException as e:
                logger.exception(
                    "ModbusPlugin: Failed to connect %s" %
                    client['uri'])
                result = 'error'
            except Exception as e:
                logger.exception("ModbusPlugin: Failed to write_register")
                result = 'error'

        return {'code': ret_code, 'data': result}

    def write_register(self, uri, address, value):
        ret_code = 1
        result = 'device not found'

        client = self._fetch_client(uri)
        if client:
            try:
                rq = client['client'].write_register(address, value)
                if rq.function_code < 0x80:
                    ret_code = ReturnCodes.Good
                    result = 'OK'
                else:
                    result = 'failed with function_code%s' % rq.function_code
            except ConnectionException as e:
                logger.exception(
                    "ModbusPlugin: Failed to connect %s" %
                    client['uri'])
                result = 'error'
            except Exception as e:
                logger.exception("ModbusPlugin: Failed to write_register")
                result = 'error'

        return {'code': ret_code, 'data': result}

    def read_coils(self, uri, address, count):
        ret_code = 1
        result = 'device not found'

        client = self._fetch_client(uri)
        if client:
            try:
                rr = client['client'].read_coils(address, count)
                if rr.function_code < 0x80:
                    ret_code = ReturnCodes.Good
                    result = str(rr.bits[0:count])
                else:
                    result = 'failed with function_code%s' % rr.function_code
            except ConnectionException as e:
                logger.exception(
                    "ModbusPlugin: Failed to connect %s" %
                    client['uri'])
                result = 'error'
            except Exception as e:
                logger.exception("ModbusPlugin: Failed to read_coils")
                result = 'error'

        return {'code': ret_code, 'data': result}

    def read_discrete_inputs(self, uri, address, count):
        ret_code = 1
        result = 'device not found'

        client = self._fetch_client(uri)
        if client:
            try:
                rr = client['client'].read_discrete_inputs(address, count)
                if rr.function_code < 0x80:
                    ret_code = ReturnCodes.Good
                    result = str(rr.bits[0:count])
                else:
                    result = 'failed with function_code%s' % rr.function_code
            except ConnectionException as e:
                logger.exception(
                    "ModbusPlugin: Failed to connect %s" %
                    client['uri'])
                result = 'error'
            except Exception as e:
                logger.exception(
                    "ModbusPlugin: Failed to read_discrete_inputs")
                result = 'error'

        return {'code': ret_code, 'data': result}

    def read_holding_registers(self, uri, address, count):
        ret_code = 1
        result = 'device not found'

        client = self._fetch_client(uri)
        if client:
            try:
                rr = client['client'].read_holding_registers(address, count)
                if rr.function_code < 0x80:
                    ret_code = ReturnCodes.Good
                    result = str(rr.registers[0:count])
                else:
                    result = 'failed with function_code%s' % rr.function_code
            except ConnectionException as e:
                logger.exception(
                    "ModbusPlugin: Failed to connect %s" %
                    client['uri'])
                result = 'error'
            except Exception as e:
                logger.exception(
                    "ModbusPlugin: Failed to read_holding_registers")
                result = 'error'

        return {'code': ret_code, 'data': result}

    def read_input_registers(self, uri, address, count):
        ret_code = 1
        result = 'device not found'

        client = self._fetch_client(uri)
        if client:
            try:
                rr = client['client'].read_input_registers(address, count)
                if rr.function_code < 0x80:
                    ret_code = ReturnCodes.Good
                    result = str(rr.registers[0:count])
                else:
                    result = 'failed with function_code%s' % rr.function_code
            except ConnectionException as e:
                logger.exception(
                    "ModbusPlugin: Failed to connect %s" %
                    client['uri'])
                result = 'error'
            except Exception as e:
                logger.exception(
                    "ModbusPlugin: Failed to read_input_registers")
                result = 'error'

        return {'code': ret_code, 'data': result}

    def read_inputs(self, client, valid_inputs, datatype):
        result = None
        try:
            inputs_bits = [0] * len(valid_inputs)
            offset = 0
            for inputs in valid_inputs:
                if datatype is MBDataType.DISCRETE_INPUTS:
                    rr = client.read_discrete_inputs(int(inputs[0]), 1, unit=1)
                else:
                    rr = client.read_coils(int(inputs[0]), 1, unit=1)
                # Test to generate random value, remove if the modus server is ready
                # seed = random.randint(0, 1)
                inputs_bits[offset] = 1 if rr.bits[0] else 0
                offset += 1
            result = inputs_bits
        except ConnectionException as e:
            logger.exception("ModbusPlugin: Failed to connect")
        except Exception as e:
            logger.exception("ModbusPlugin: Failed to read inputs")

        return result

    def read_registers(self, client, valid_registers, datatype):
        result = None
        try:
            rr_data = [0] * len(valid_registers)
            offset = 0
            for registers in valid_registers:
                if datatype is MBDataType.INPUT_REGS:
                    rr = client.read_input_registers(
                        int(registers[0]), 1, unit=1)
                else:
                    rr = client.read_holding_registers(
                        int(registers[0]), 1, unit=1)
                rr_data[offset] = rr.registers[0]
                offset += 1
            result = rr_data
        except ConnectionException as e:
            logger.exception("ModbusPlugin: Failed to connect")
        except Exception as e:
            logger.exception("ModbusPlugin: Failed to read registers")

        return result

    def notify_data(self, data, node):
        if data is not None:
            pair_variable = node.get_pair_friend()
            parent = node.get_parent()
            self.pub_data(parent.name, pair_variable.name, data)

    def _plugin_main(self, *args, **kwargs):
        now = 0
        # Wait 1s to mqservice ready
        time.sleep(1)
        while not self.is_stop:
            for client in self.modbus_clients.values():
                if not client['predefined']:
                    continue

                device_node = client['node_data']
                period_node = self.entity.get_property(device_node, 'period')
                if period_node is None:
                    continue

                if now % int(period_node.value) == 0:
                    if not client['connected']:
                        client['client'].close()
                        client['connected'] = client['client'].connect()
                        if not client['connected']:
                            continue

                    node = self.entity.get_property(device_node, 'valid coils')
                    if node and node.value:
                        data = self.read_inputs(
                            client['client'], node.value, MBDataType.COILS)
                        self.notify_data(data, node)

                    node = self.entity.get_property(
                        device_node, 'valid discrete inputs')
                    if node and node.value:
                        data = self.read_inputs(
                            client['client'], node.value, MBDataType.DISCRETE_INPUTS)
                        self.notify_data(data, node)

                    node = self.entity.get_property(
                        device_node, 'valid holding registers')
                    if node and node.value:
                        data = self.read_registers(
                            client['client'], node.value, MBDataType.HOLDING_REGS)
                        self.notify_data(data, node)

                    node = self.entity.get_property(
                        device_node, 'valid input registers')
                    if node and node.value:
                        data = self.read_registers(
                            client['client'], node.value, MBDataType.INPUT_REGS)
                        self.notify_data(data, node)

                    if data is None:
                        client['connected'] = False

            now += 1
            time.sleep(1)


def plugin_main(*args, **kwargs):
    plugin_entity = ModbusPluginEntity(args[0])
    plugin_config = ModbusPluginConfig(args[1])
    plugin_client = ModbusPluginClient(plugin_entity, plugin_config)
    plugin_client.start()
