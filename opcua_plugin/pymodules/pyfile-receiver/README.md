# pyfilesys

## Description

pyfile-receiver plugin provide Raw Data OPC UA variable node with image information and provide fread method to Client to read specify image file

## Language

Python

## Configuration

The following properties can be configured by editing `plugin_file_receiver.json`:

    Raw Data
        this variable node is used to expose some information for image via OPC UA

    Mqtt Broker
        specify mqtt broker address/port

    Mqtt Topic
        specify mqtt topic for refs variable, auto to write refs node from this mqtt topic message

    Image Folder
        specify folder path name which will be shared via OPC UA with read access. e.g. "./images/"

## OPC UA Methods

The plugin will provide following OPC UA methods:

    fread
        read file with specify filename 

## Test

To run the plugin, add `pymodules/pyfile-receiver` into `modules.conf` and restart all services.

## internals

