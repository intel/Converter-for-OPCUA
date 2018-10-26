# py27opc

## Description
The plugin provide remote opc server data access on OPC UA

## Language
Python

## Configuration

## OPC UA Methods

The plugin will provide following OPC UA methods:

    read
        read data from opc server
            arg1 : data tag for opc server

    write
        stop a plugin
            arg1 : data tag for opc server
            arg2: data value

## TEST
To run the plugin, add 'pymodules/py27opc' into 'modules.conf' and restart all services. 

## Internals
