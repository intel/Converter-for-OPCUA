# pyfilesys

## Description

pyfilesys plugin provide read/write file method from a local hard disk via OPC UA

## Language

Python

## Configuration

The following properties can be configured by editing `plugin_filesys.json`:

    folder
        specify folder path name which will be shared via OPC UA with read/write access. e.g. "./images/"

## OPC UA Methods

The plugin will provide following OPC UA methods:

    fread
        read file with specify filename 

    fwrite
        write file with specify filename

## Test

To run the plugin, add `pymodules/pyfilesys` into `modules.conf` and restart all services.

## internals

