# Running Functional Tests

## Description

test all plugins by python

## Language

Python

## Configuration

## Test Plugin

1. Mqtt

	* Run source code, recieves message by "raw" or "alarm"

		$ python3 test_methods_mqtt.py <"raw" or "alarm">

	* Result

		"raw" recieves message "Raw Data", "alarm" recieves message "Alarm".

2. Modbus TCP

	* Start modbus simulator

		reference README.md in plugin Modbus-Tcp

	* Run source code

		$ python3 test_methods_modbus_tcp.py

	* Result

		$test ping api

		$method result is:  ['0', 'pong']

		$test refresh api

		$method result is:  ['16384', 'No yet implemented in this Plugin']

		$test getstate api

		$method result is:  ['0', '["{\\"name\\": \\"127.0.0.1:5020\\", \\"connected\\": \\"connected\\"}", "{\\"name\\": \\"127.0.0.2:5020\\", \\"connected\\": \\"disconnected\\"}"]']

		$test connect 127.0.0.1:5020

		$method result is:  ['0', 'connect success']

		$test write_coil

		$method result is:  ['0', 'OK']

		$test read_coils

		$method result is:  ['0', '[True, True, True, True, True, True, True, True, True, True]']

		$test read_discrete_inputs

		$method result is:  ['0', '[True, True, True, True, True, True, True, True, True, True]']

		$test write_register

		$method result is:  ['0', 'OK']

		$test read_holding_registers

		$method result is:  ['0', '[17, 17, 17, 17, 17, 17, 17, 17, 17, 17]']

		$test read_input_registers

		$method result is:  ['0', '[17, 17, 17, 17, 17, 17, 17, 17, 17, 17]']

		$test disconnect

		$method result is:  ['1', 'disconnect not allow']

3. SCPI

	* Edit test_methods_scpi.py

		$ "tcp:127.0.0.1:80": <scpi ip and port>

	* Run source code

		$ python3 test_methods_scpi.py

	* Result

		$test scpi open @tcp:127.0.0.1

		$method result is:  ['0', 'connection tcp:127.0.0.1:80 was opened']

		$test scpi state @tcp:127.0.0.1

		$method result is:  ['0', 'opened']

		$test scpi send @tcp:127.0.0.1

		$method result is:  ['0', "return data-b'TST123' from 127.0.0.1"]

		$test scpi close @tcp:127.0.0.1

		$method result is:  ['0', 'socket connection tcp:127.0.0.1:80 was closed']

4. DB-KV

	* Run source code

		$ python3 test_methods_kv.py

	* Result

		$test kv put data1

		$method result is:  ['0', 'OK']

		$test kv get data1

		$method result is:  ['0', 'value:10']

		$test kv delete data1

		$method result is:  ['0', 'OK']

5. Filesys

	* Run source code

		$ python3 test_methods_file.py

	* Result

		$test fread api - read 4.bmp

		$method result code is:  16384

		$test fread api - read 6.bmp

		$method result code is:  16384

6. File-receiver

	* Run test_methods_file_receiver_fread.py

		$ python3 test_methods_file_receiver_fread.py 1

	* Result

		$test fread api - read 1.bmp

		$method result code is:  16384

	* Run test_methods_file_receiver_rawdata.py

		& python3 test_methods_file_receiver_rawdata.py 1000

	* Result

		It recieves images by "Raw Data"

7. OPC

	* Run test_methods_opc.py

		$ python3 test_methods_opc.py

	* Result

		$test write

		$method result is:  ['0', 'The operation completed successfully.']

		$test read, it should receive the PI value since we write to 0

		$method result is:  ['0', '{"quality": "Good", "ts": "09/13/18 16:37:47", "val": 3.14159268452}']

		$Python: New data change event Node(NumericNodeId(ns=2;i=26)) {"code": 0, "data": "{\"quality\": \"Good\", \"ts\": \"09/13/18 16:37:51\", \"val\": 26500}"}

