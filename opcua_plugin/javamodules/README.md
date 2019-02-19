# Java Plugins

We provide sample Java plugins to show how a Java plugin work for
`Converter for OPC UA`, however they are not functionally complete as other
plugins.

# Building

[Apache Maven](http://maven.apache.org/) is used to build Java plugins.

```bash
$ mvn clean package
```

# Running

Use `loader.sh` script to run the plugin:

```bash
$ ./loader.sh <plugin_folder_name>
```

After loading the plugin, you can check the registered Nodes using any OPC-UA clients.

# Developing Java Plugins

We provides a base class for plugin developers to inherit from and override
key functions. Please check source code of sample plugins `modbus` and `mqtt`.

NOTICE: The Java plugin sample code provided is intended for teaching
how to develop the plugin. They are currently not functional modbus or mqtt plugins.