# FAQ

## 1. How to configure AMQP server address?

Converter for OPC-UA is using AMQP bus to do data interaction between opcua-converter and plugins, the default AMQP broker is using `amqp://guest:guest@127.0.0.1`. You can to modify it by yourself as below:

a. For opcua-converter: you can find relate configuration in `pyutilities/configger/default.conf`

Sample:     

	[Amqp]
	   url = amqp://<user>:<password>@<AMQP broker IP address>
 
b. For plugins: you can find relate configuration in `opcua_plugin/pymodules/<plugin name>/default.conf`

Sample:     

	[Amqp]
	   url = amqp://<user>:<password>@<AMQP broker IP address>
 
## 2. How to configure logging configuration?

Logging configuration directory is:

a.	For opcua_converter:

	pyutilities/configger/default.conf

b.	For opcua_plugin:

	opcua_plugin/pymodules/<plugin name>/default.conf

Logging configuration options:

a.	`path`: the path is logging path to save to disk

b.	`maxbytes`: single logging file size

c.	`file_count`: logging is supporting rotate to save logging to disk, `file_count` is using to configurate max logging file count

d.	`format`: it is reserved to configurate logging format, the current is only support standard

e.	`level`: it is used to configurate logging level, critical/error/warning/info/debug are supported

For plugins:

  `type` is using to configurate logging output path, console/file/all/none are be configurated
 
## 3. How to configure data type with variable node?

The data type of the variable is automatically determined based on the first incoming value, the current it is not supported to be configurated by JSON. As one solution ,we suggest to use `init_value` for expected data type
 
## 4. How to make sure that nodeid don't change with multi-plugins online disorder?

With multi-plugins, it is difficult to make sure the online order don't change for every plugin, so we suggest to use different `uri_name`  to define different namespace, you can configurate `uri_name` in plugin JSON file.

## 5. How to run plugin with shell?

When you are using shell to run plugin, you must go to opcua_plugin directory firstly, then run `python3 pymodule/loader.py pymodule/<plugin name>` command to run plugin.

## 6. How to check the result?

You can use any OPC-UA client to enumerate nodeid,which will help you to check your result, [opcua-client-gui](https://github.com/FreeOpcUa/opcua-client-gui) is recommended

## 7.  How to create plugin configuration file?

Please refer to opcua_plugin/pymodules/pyfilesys/default.conf


