# Plugin Configuration

A plugin consists of two configuration files:

1. Plugin description (.json) is a JSON formatted file  including the protocol standard, description version, and user data.

2. Configururation file (.conf) for information, security and connection information.

For example, a typical plugin file structure is as follows:
```pymodbus-tcp
├── default.conf
├── plugin_main.py
├── plugin_modbus.json
├── README.md
└── unittest
```

`default.conf` is the plugin configuration file. `plugin_modbus.json` is the Entity file that defines opcua.

**In addition, the plugin reads the configuration file according to the suffix name of the file. So in a plugin directory, only one.conf and one.json file are allowed.**

For built-in plugins, the default configuration works well most of the time. But if you need more detailed control information, you may need to customize it. 

## Basic Configuration Information
The conf configuration file is Windows-INI-style (Python ConfigParser)  file, containing only paragraphs [Logging].
Examples are as follows:
```ini
[Logging]
    #console, file, all, none
    type = console
    file = /var/log/opcua/kvplugin.log
    maxbytes = 10485760
    level = debug
```

### [Logging]
Log information for configuring plugins. Contains the following key:

##### type
Log output target contains four values:

1. console:just printing log to the standard output of the front console. only for debugging
2. file:printing log to the target file.
3. all:both the front console and the target file record logs.
4. none:no output log

##### file
The target file output by log is valid only when type is set to file or all.

##### maxbytes
The maximum number of bytes of target files output by log is valid only when type is set to file or all.

##### level
Log output level.

---

## Entity Configuration
When the plugin starts, a node will be registered on the opcua server. The information of this node is obtained from this entity configuration file.
The configuration file is a standard json format file on the top level of the plugin directory, referring to [the basic configuration of plugins](docs/plugin_configuration.md).

### Plugin Description Format Definition
A typical top-level plugin description is a JSON formatted file (.json) including the protocol standard,
description version, and user data, currently in this project only opcua protocol is supported.

| Property | Description |
| ------ | ------ |
| di | description information (alternatively `di`) |
| st | protocol standard (alternatively `st`), eg: opcua |
| version | version (alternatively `ver`) |
| status | status |
| links | reference utilities |
| user_data | user defined data |
| user_data.name | plugin name |
| user_data.topic | amqp bus topic |
| user_data.apilist | apis supported by this plugin |
| user_data.opcua | the protocol data defined in `st` |


A typical opcua folder layout is as below, in general, plugin developer needs to define one or more custom types for each new plugin, and in the opcua root folders, define the objects of opcua native variable, property, method, and the customer types.

| Property | Description |
| ------ | ------ |
| user_data.opcua.endpoint_path | ocpua server address "opc.tcp://0.0.0.0:4840/freeopcua/server/" |
| user_data.opcua.uri_name | the website url for example "http://examples.freeopcua.github.io" |
| user_data.opcua.custom_types | the customized opcua data structure list |
| user_data.opcua.folders | the opcua root folders. the opcua sub folders which can include opcua native defined variable, property, method and also the custom_types defined by the user |

If you want to write a plugin yourself, you should be familiar with the format of the entity configuration file. A complete entity file may be a bit complicated, but you don't need to know all the attribute values.
If you want to write a plugin yourself or modify a plugin, you'd better copy an entity file from a complete example, and then just modify what you care about.

A typical example is as follows:
```json
{
  "di":"SCPI",
  "st":"OPCUA",
  "version":"1.0.2",
  "status":"on",
  "links":[],
  "user_data":
  {
    "name":"KvPlugin",
    "topic":"req/KvPlugin",
    "apilist":[
      {"name": "getrd", "output": ["String"]},
      {"name": "ping", "output": ["String"]},
      {
        "name": "getstate",
        "input": [{"type": "String", "default": null}],
        "output": ["String"]
      },
      {"name": "refresh", "output": ["String"]}
    ],
    "opcua":
    {
      "endpoint_path":"opc.tcp://0.0.0.0:4840/freeopcua/server/",
      "uri_name":"http://examples.freeopcua.github.io",
      "broker_path":"/proxy/KvPlugin",
      "custom_types":
      [
        {
          "name":"KvDBType"
        }
      ],
      "folders":
      [
        {
          "name":"KvPlugin",
          "KvDBType":
          [
            {
              "name":"KvDB",
              "properties":
              [
                {
                  "name":"DBFileFolder",
                  "value":"leveldb"
                }
              ]
            }
          ],
          "methods":
          [
            {
              "name":"put",
              "rpc_name":"put",
              "input":[{"name":"key","type":"String"}, {"name":"value","type":"String"}],
              "output":["String"]
            },
            {
              "name":"get",
              "rpc_name":"get",
              "input":[{"name":"key","type":"String"}],
              "output":["String"]
            },
            {
              "name":"delete",
              "rpc_name":"delete",
              "input":[{"name":"key","type":"String"}],
              "output":["String"]
            }
          ]
        }
      ]
    }
  }
}
```

### Attributes Description

#### user_data['name']
The name of the plugin.

**Please keep this property consistent with user_data['opcua']['folders'][0]['name'].**

#### user_data['opcua']['custom_types']
Each plugin will register a new custom type object type on the opcua server. Subsequently, the type of object associated with the plugin is defined here. You can use a legal name to define a custom type.

#### user_data['opcua']['folders']
This is designed to be a list for the purpose of possible expansion. The definition in this list will be registered as a node to the opcua server.
Generally speaking, a plugin works well with only one node, and to avoid complexity, it is recommended to keep the list 1 in length.

The single option value in List is the following example:
```json
{
  "name":"PluginName",
  "{CustomeTypeName}": [],
  "methods": []
}
```

##### name
The name option is the name displayed by the registered node.

##### {CustomTypeName}
`CustomTypeName` is the custom object type name mentioned earlier, just keep it consistent with the custom type name.
If you need to register an object on the opcua server, just refer to the example above to fill in the object properties in the list.

##### methods
The plugin's respective methods are defined here. The following example shows:
```json
{
  "name":"put",
  "rpc_name":"put",
  "input":["String", "String"],
  "output":["String"]
}
```

`name` is the method name.
`rpc_name` is for retention purposes, please keep the same as name.
`input` is the parameter accepted by the method, expressed in list. The example above shows the parameters that accept two string types. **Converter for OPC-UA** will make corresponding internal transformation. The result of the transformation is shown in the following table (take Python data type as an example):
```
'String': str,
'string': str,
'str': str,
'int': int,
'Int': int,
'Integer': int,
'Long': int,
'long': int,
'Float': float,
'float': float,
'Double': float,
'double': float,
'Bool': bool,
'bool': bool,
```
`output` represents the return value of the method, similar to that of input.

**Note: the return value only accepts string types. The **Converter for OPC-UA** attempts to convert and return to opcua client, which may not get the correct result if it returns a value of a non-string type.**
