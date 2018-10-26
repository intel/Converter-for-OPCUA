# Console

To run interactive command line console, you need to enable `manager` plugin firstly and use manager to run all plugins, please run:
    python3 pyutilities/serve/standalone.py

Then to start interactive console, run:

	$ python3 tests/tools/console.py

When the console tool run successfully, you will see

	(opcua plugin tool) > 

## help: command help

    Documented commands (type help <topic>):
    ========================================
    help
    
    Undocumented commands:
    ======================
    call  exit  getcfg  plugin_list  setcfg  start_plugin  stop_plugin  tree


## plugin_list: display all plugin status

    (opcua plugin tool) > plugin_list
    [{'status': 'STOPPED', 'name': 'ModbusPlugin-TCP'}, {'status': 'STOPPED', 'name': 'MqttPlugin'}, {'status': 'STOPPED', 'name': 'KvPlugin'}, {'start_time': '0day 0hour 5min 12s', 'status': 'Started', 'name': 'manager'}]


## start_plugin: start a plugin by name

    (opcua plugin tool) > start_plugin KvPlugin
    OK


## stop_plugin: stop a plugin by name

    (opcua plugin tool) > stop_plugin KvPlugin
    OK


## getcfg: get the config file from plugin

    (opcua plugin tool) > getcfg MqttPlugin json /home/test_user/test/
    saved file to /home/test_user/test/plugin_mqtt.json


## setcfg: upload the config file to plugin

    (opcua plugin tool) > setcfg MqttPlugin conf /home/test_user/test/plugin_mqtt.json
    OK

## call: call plugin method

    (opcua plugin tool) > call KvPlugin put key value
    ['0', 'OK']


## tree: list tree structure of the plugin nodes
    (opcua plugin tool) > tree KvPlugin
    KvPlugin
    |---KvDB
        |---DBFileFolder
    |---put
        |---InputArguments
        |---OutputArguments
    |---get
        |---InputArguments
        |---OutputArguments
    |---delete
        |---InputArguments
        |---OutputArguments
    |---getrd
    |---ping
    |---getstate
    |---refresh
