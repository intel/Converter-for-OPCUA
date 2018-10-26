# Building and Running C Plugins

# Building

`cmodbus-serial` plugin is written in C language, it is necessary to compile the code first.

First install the `libmodbus-dev` library:
```bash
$ sudo apt-get install libmodbus-dev==3.0.6
```
Then build all C plugins:

```bash
$ cd opcua_plugin/cmodules
$ make
```

# Running

Modify the configuration file `plugin_modbus.json` in `opcua_plugin/cmodules/cmodbus-serial`, change `device address` attribute to IP and port of the modbus device.

Edit `opcua_plugin/modules.conf` to start `cmodbus-serial` with the Converter or you can manually start the plugin, run:

```bash
$ cd opcua_plugin/cmodules/cmodbus-serial
$ ./plugin_cmodbus-serial plugin_modbus.json
```
