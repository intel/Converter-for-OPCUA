# manager

## Description
Used to manage or configuration of other plugins. 

## Language
Python

## Configuration

## OPC UA Methods

The plugin will provide following OPC UA methods:

    get_plugin_list
        get a list of all plug-ins for this machine.
    
    start_plugin
        start a plugin
            arg1 : plugin name (Same as JSON file definition)

    stop_plugin
        stop a plugin
            arg1 : plugin name (Same as JSON file definition)

    getcfg
        Get configuration file content from plugin
            arg1: plugin name (Same as JSON file definition)
            arg2: conf | json 
                conf: configuration file
                json: opcua entity file

    setcfg
        Upload configuration files to plugin
            arg1: plugin name (Same as JSON file definition)
            arg2: conf | json 
                conf: configuration file
                json: opcua entity file
             arg3: file content as string

## TEST
To run the plugin, please run "python3 pyutilities/serve/standalone.py".

## Internals
