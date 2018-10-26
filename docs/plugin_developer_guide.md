# Plugin Developer Guide

## Introduction
**Converter for OPC-UA** provides several plugins for common scenarios, such as modbus/mqtt connection. In most cases, these built-in plugins can meet your needs.
But in many cases, you may still need to write plugins that meet your needs.

## Develop custom plugins
To implement a plugin, we need to do the following things:

- Understand the structure of plugins
- Prepare configuration files to complete the definition of opcau protocol
- Implement code

### Plugin structure
It only needs an ordinary folder, which contains three files.
The simplest plugin directory structure is as follows, take the pymqtt plugin as an example:
```pymqtt
├── default.conf
├── plugin_main.py
├── plugin_mqtt.json
```

`default.conf` and `plugin_mqtt.json` are related [configuration files](docs/plugin_configuration.md). `plugin_main.py` is the implementation code of plugin. 

When all the files are ready, the plugin home folder will be placed in the appropriate source directory, and then start the validation.

Up to now, the source directory of plugins is fixed. $SOURCE_CODE/opcua_plugin.

Related plugins written in Python are located $SOURCE_CODE/opcua_plugin/pymodules.

For starting and validating plugins, please refer to [plugin](docs/plugin.md).

### Preparing configuration files
You need to prepare two configuration files to make the plugin work properly. The type of configuration file is determined by file extension, `.conf` file is the basic configuration (log, connection information), `.json` is the opcua definition file.

For detailed configuration notes, please refer to [configuration files](docs/plugin_configuration.md).

You don't need to reconfigure configuration files. The recommended practice is to copy a copy from other template files and make corresponding modifications.

### Sample
Let's take an example of reading CSV files plugin.
The basic configuration file is as follows:
```ini
[Logging]
    type = console
    file = /var/log/opcua/csv-plugin.log
    maxbytes = 1024000
    level = debug
[Security]
    tls = false
    cafile =
    cerfile =
    keyfile =
```

#### Opcua related definition
It is recommended to supplement the contents from a template file.
A simple json template file is as follows:
```json
{
  "di":"SCPI",
  "st":"OPCUA",
  "version":"1.0.2",
  "status":"on",
  "links":[],
  "user_data":
  {
    "name":"{% plugin name %}",
    "topic":"req/{% plugin name %}",
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
      "broker_path":"/proxy/{% plugin node custom type name %}",
      "custom_types":
      [
        {
          "name":"{% plugin node custom type name %}"
        }
      ],
      "folders":
      [
        {
          "name":"{% plugin name %}",
          "{% plugin node custom type name %}":
          [
            {
              "name":"{% plugin node name %}",
              "methods":
              [
                "{% methods %}"
              ]
            }
          ]
        }
      ]
    }
  }
}
```

Please note the content marked in {%  %} in the template file. We only need to add the contents of {%  %} to complete a simple definition.

Let's first implement a simplest plugin example. In the first step, this plugin only needs to read the first line of the CSV file and return it.
So for the opcua definition, we just need to define a CSV node and a read method for that node. So the json file is completed as follows:
```json
{
  "di":"SCPI",
  "st":"OPCUA",
  "version":"1.0.2",
  "status":"on",
  "links":[],
  "user_data":
  {
    "name":"CsvPlugin",
    "topic":"req/CsvPlugin",
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
      "broker_path":"/proxy/CsvPlugin",
      "custom_types":
      [
        {
          "name":"CsvType"
        }
      ],
      "folders":
      [
        {
          "name":"CsvPlugin",
          "CsvType":
          [
            {
              "name":"CsvNode"
            }
          ],
          "methods":
          [
            {
              "name":"read",
              "rpc_name":"read",
              "input":[],
              "output":["String"]
            }
          ]
        }
      ]
    }
  }
}
```

In this configuration file, we define a plugin called `CsvPlugin`. Because the object node of the plugin is designed to be a custom type, so we also define a custom type of `CsvType`.
Based on this type, a CsvNode opcua object node is defined. The node then defines a `read` method that accepting argument is null and output is a `String` (temporarily, only the outputting string results are supported, and most of the requirements can still be met through the corresponding serialization transformation)

For detailed opcua json configuration, please refer to [configuration file](docs/plugin_configuration.md).

### code implementation

In this example, the plugin does something simply, just reading the first line of output from the CSV file and returning it. The examples are as follows:

```python

    import os
    import json
    import csv
    from client import BasePluginClient
    from entity import BasePluginEntity
    from config import BasePluginConfig
    class CsvPluginClient(BasePluginClient):
      def __init__(self, entity, config):
        super(CsvPluginClient, self).__init__(entity, config)
        self.csv_fp = os.path.join(os.path.dirname(__file__), 'sample.csv')
      def read(self):
        ret_code = 0
        result = ""
        with open(self.csv_fp, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                result = json.dumps(row)
                break
        return {'code': ret_code, 'data': result}
      def plugin_main(*args, **kwargs):
        plugin_entity = BasePluginEntity(args[0])
        plugin_config = BasePluginConfig(args[1])
        plugin_client = CsvPluginClient(plugin_entity, plugin_config)
        plugin_client.start()
```

We need to inherit the `BasePluginClient` base class, which does some basic processing, such as server communication connections, declaration cycle management, and so on. At present, we simply need to inherit it.

In addition, we need to implement the plugin's own read function. We simply define a `read` function that returns the first line of the CSV file.

Moreover, we need to implement a `plugin_main` method. This is the plugin's entry function called when the plugin is started, and its handling is to initialize the instance and call the start method of the plugin object.

** Note that the return type of the method is a python dictionary, {"code": Return code >, data: return string}, and we require the return value data to be a string.**

### Program improvement (add parameter in function, configure node attribute)
In above program, we read the sample.csv file in the relative directory and return to the first row. Let's make some improvements.

1. The read method adds a parameter to specify which line to read.
2. The sample.csv source file path is modified to obtain by configuration property.

#### Program improvement - modify read function parameters
Modifying function parameters is very simple. We want the parameters to be passed into the `read` function to be of type `Int`, just to change the json file that configures the read function to look like this:
```json
  "methods":
  [
    {
      "name":"read",
      "rpc_name":"read",
      "input":["Int"],
      "output":["String"]
    }
  ]
```

The SDK converts data based on configuration parameters. For support function parameter type conversion, please reference to [plugin_configuration](docs/plugin_configuration.md). It lists all the transferable types.

Then modify the implementation of the read function:

```python

    def read(self, line_num):
      ret_code = 0
      result = ""
      with open(self.csv_fp, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if reader.line_num == line_num:
                result = json.dumps(row)
                break
      return {'code': ret_code, 'data': result}
```

The input parameter of the `read` method in the json file configures an output parameter of type int, which is passed to the implementation of the read function and automatically converted to type int. So we can use it directly in code implementation.

#### Program improvement - add attribute configuration and configure the location of the CSV file
In the above example, the CSV file we read is based on the relative path. Let's assume that the file location is configurable, so let's show you how to configure an opcua node property on the SDK and use it.

Firstly, the configuration file is modified as follows. We add an attribute named `csvPath` to the `CsvNode` node. The value of the attribute is the absolute path of the CSV sample file (also the relative path can be used, and finally the program code can handle it freely).
```json
  "CsvType":
  [
    {
      "name":"CsvNode",
      "properties":
      [
        {
          "name":"csvPath",
          "value":"/home/test/sample.csv"
        }
      ]
    }
  ]
```

To get this attribute in code, we first need to get the CsvNode node through the interface. Two API interfaces are needed here:entity.get_custom_nodes() and entity.get_property()

The revised code is as follows:

```python

    def __init__(self, entity, config):
      super(CsvPluginClient, self).__init__(entity, config)
      self.csv_node = self.entity.get_custom_nodes()[0]
      self.csv_fp = self.entity.get_property(self.csv_node, 'csvPath').value
      # self.csv_fp = os.path.join(os.path.dirname(__file__), 'sample.csv')
```

`get_custom_nodes` will get all the custom_node nodes in the json configuration file. Please refer to our json configuration file above. We have defined a list with only one element.
So `self.entity.get_custom_nodes()[0]` will get the only reference to the custom_node node.
Then we get the value of `csvPath` through the `get_property` interface.

#### Program improvement - increase opcua variable variables
To illustrate the usage of variables, we assume that such a scenario is also the above example. We add a new variable to the csvnode to count the number of calls to the read method. Each time the read function is called, we want to update it to the custom opcua variable.

```json
  "custom_types":
  [
    {
      "name":"CsvType",
      "variables":
      [
        {
          "name":"read_count",
          "type":"String",
          "historizing":
          {
            "period": 2,
            "count":300
          },
          "writable":"yes"
        }
      ]
    }
  ]
```

Adding variables requires the definition of custom_types node. In this example, we define a custom `CSvType` type and define a variable with the `read_count` name.

The opcua node object based on this type then has a `read_count` variable, which is writable. `historizing` is the persistence information that sets variables on the opcua server.

Then we need to implement the code to update this variable. Every time we execute the read method, we notify the server to update the variable data through a API interface.

```python

    def __init__(self, entity, config):
      super(CsvPluginClient, self).__init__(entity, config)
      self.csv_node = self.entity.get_custom_nodes()[0]
      self.csv_fp = self.entity.get_property(self.csv_node, 'csvPath').value
      self.read_count = 0

    def read(self, line_num):
      ret_code = 0
      result = ""
      self.read_count += 1
      with open(self.csv_fp, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if reader.line_num == line_num:
                result = json.dumps(row)
                break
      self.pub_data(self.csv_node.name, "read_count", str(self.read_count))
      return {'code': ret_code, 'data': result}
```

The `pub_data` interface method of `BasePluginClient` is used to update variable data. Note that all three parameters of the `pub_data` method must be strings, so we need to do the necessary type conversion.
The three parameters are the name of the opcua node node, the variable name of the node, and the variable value.

#### Program improvement - lifecycle management
Some plugins need to do the initial work, such as starting a new thread in the CSV plugin, constantly checking which files have been modified. Another example is a plugin for MySQL, which needs to connect to MySQL server when the plugin starts.

All plugins are based on subclasses of `BasePluginClient` class. The parent class has done some basic processing, such as program startup, preparation of communication links, etc. Its entry function is the start method.
But the parent start main thread cannot be blocked, so if you need to do some connection or other blocking. It is recommended to start a new thread in the subclass implementation to complete it.

Just override the start method, add your own implementation code, and finally make sure to call the start method of the parent class.

The last complete Python sample is implemented as follows:

```python

    class CsvPluginClient(BasePluginClient):
    def __init__(self, entity, config):
        super(CsvPluginClient, self).__init__(entity, config)
        self.csv_node = self.entity.get_custom_nodes()[0]
        self.csv_fp = self.entity.get_property(self.csv_node, 'csvPath').value
        # self.csv_fp = os.path.join(os.path.dirname(__file__), 'sample.csv')
        self.read_count = 0

    def _start(self):
        #connect somethings or new thread
        pass

    def _stop(self):
        #close somethings
        pass

    def start(self):
        self._start()
        super(CsvPluginClient, self).start()

    def stop(self):
        self._stop()
        super(CsvPluginClient, self).stop()

    def restart(self, *args, **kwargs):
        self._stop()
        self._start()

    def read(self, line_num):
        ret_code = 0
        result = ""
        self.read_count += 1

        with open(self.csv_fp, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if reader.line_num == line_num:
                    result = json.dumps(row)
                    break
        self.pub_data(self.csv_node.name, "read_count", str(self.read_count))
        return {'code': ret_code, 'data': result}
```
