# pydb-kv

## Description
The plugin provide access leveldb

## Language
Python

## Configuration

## OPC UA Methods

The plugin will provide following OPC UA methods:

    put
        put data to leveldb
            arg1 : data key
            value : data value

    get
        get data from leveldb
            arg1 : data key

    delete
        delete data 
            arg1 : data key

## TEST
To run the plugin, add 'pymodules/pydb-kv' into 'modules.conf' and restart all services.

## Internals
