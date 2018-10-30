# Plugins

## Using Plugins

### Start Plugins
There are 3 ways to start a plugin.

1. Start with the Converter
   
Edit `opcua_plugin/modules.conf` to add plugins you want to run before starting the converter. 
 
2. Start manually
   
The following example shows how to start a built-in `pymqtt` plugin.
```bash
$ cd opcua_plugin
$ python3 pymodules/loader.py pymodules/pymqtt 
```

3. Use [Plugin Manager](../opcua_plugin/pymodules/manager/README.md) to start a plugin

Firstly, run the management program to start Plugin Manager:

```bash
$ python3 pyutilities/serve/standalone.py
```
Plguin Manager provides a standard OPC-UA interface to manage plugins. The plugin can be controlled by calling the corresponding API interface, such as starting or stopping etc. You can use any OPC-UA client to access those interfaces such as [opcua-client-gui](https://github.com/FreeOpcUa/opcua-client-gui).
We also provide a [Console](docs/console.md) tool  that allows you to control plugins quickly.
To start the built-in pymqtt plugin using the console tool:

```bash
$ python3 tests/tools/console.py
Welcome to the (opcua plugin tool) shell.
Type help or ? to list commands.
(opcua plugin tool) > 
```

When you start, you will see the above message. Then start the plugin:

```bash
(opcua plugin tool) > start_plugin MqttPlugin
OK
```

Please check [Console](docs/console.md) for usages.

### Building and Running C Plugins

You may need to build C plugins before use. Check [opcua_plugin/cmodules/README.md](../opcua_plugin/cmodules/README.md) for details.

### Default Plugin List

The following plugins are included by default in Converter for OPC UA.

#### Python Plugins
    py27opc
    pydataproc
    pydb-kv         
    pyfile-receiver
    pyfilesys    
    pyhd          
    pymodbus-tcp
    pymqtt       
    pyscpi   

#### C Plugins
    cmodbus-serial

Please check README.md in each plugin's directory for details.

## Configurure Plugins

A plugin consists of two configuration files:

1. Plugin description (.json) is a JSON formatted file  including the protocol standard, description version, and user data.

2. Configururation file (.conf) for information, security and connection information.

Please refer to [Plugin Configuration](plugin_configuration.md) for details.

## Developing Plugins

Please refer to [Plugin Developer Guide](plugin_developer_guide.md) for details.
