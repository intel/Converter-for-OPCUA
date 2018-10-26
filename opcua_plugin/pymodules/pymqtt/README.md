# pymqtt

## Description

pymqtt plugin receives messages of devices' information in factory. The messages are sent to edge gateway.

## Language

Python

## Configuration

The following properties can be configured by editing `plugin_mqtt.json`:

	host
		mqtt server ip

	port
		mqtt server port

	cafile
		ca.crt

	cert
		client.crt

	key
		client.key

## Setting TLS/SSL

Steps to enable TLS/SSL to MQTT server and client

1. Copy CA certificate, client certificate and private key to specify folder

2. Run Mqtt Plugin by tls

	* Edit plugin_mqtt.json

		"host": "127.0.0.1"<mqtt server ip>

		"port": "8883"

		"cafile": <'ca.crt' file path>

		"cert": <'client.crt' file path>

		"key": <'client.key' file path>

		"name": "Raw Topic"

		"refs": "Raw Data"

		"value": "topic_raw_1"<mqtt topic>

	* Run Mqtt plugin

		$ cd opcua_converter-sdk/opcua_plugin

		$ python3 pymodules/loader.py pymodules/pymqtt

3. Run Mqtt simulator

	* Copy "ca.crt, client.crt, client.key" to folder "simulator/"

	* Send message by tls

		python3 mqtt_sender.py <time intervel> <mqtt topic> --cacert=tls

		example:

		$ python3 mqtt_sender.py 1000 "topic_raw_1" --cacert=tls

		$ python3 mqtt_alarm_sender.py 1000 "topic_alarm_1" --cacert=tls

	* Else

		python3 mqtt_sender.py <time intervel> <mqtt topic>

		example:

		$ python3 mqtt_sender.py 1000 "topic_raw_1"

		$ python3 mqtt_alarm_sender.py 1000 "topic_alarm_1"

