# cmodbus-rtu

## Description

cmodbus-rtu plugin receives modbus information in factory, provides remote device control based with rtu on OPC UA

## Language

C

## Configuration

The following properties can be configured by editing `plugin_modbus.json`:

	device address
		modbus ip and port

	period
		time interval

## Simulator

1. With this command, it will create two virtual ports automatically, for example /dev/pts/19 , /dev/pts/20

	$ socat -d -d pty,raw,echo=0, pty,raw,echo=0

2. Download the modbus simulator from here http://www.modbusdriver.com/diagslave.html, Then, execute the digaslave to the second port created in the first step (here, /dev/pts/20)

in our case:

	$ unzip diagslave.2.12.zip

	$ cd linux

	$ ./diagslave -b 115200 /dev/pts/20

3. Modify the plugin_modbus.json, change the "device address" to the first port created in the first step (here, /dev/pts/19)

## Test

To run the plugin, libmodbus need to be installed first

	$ sudo apt-get install libmodbus-dev

then restart all services and run:

	$ ./plugin_cmodbus-serial plugin_modbus.json

## Internals
