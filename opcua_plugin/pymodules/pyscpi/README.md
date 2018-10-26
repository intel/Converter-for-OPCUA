# pyfilesys

## Description

pyscpi plugin provide remote SCPI device control based with tcp/serial on OPC UA

## Language

Python

## Configuration

User can configurted method/properties by editing `plugin_scpi.json`

## OPC UA Methods

The plugin will provide following OPC UA methods:

    open
        For serial: open tty device with specify parameters: 
            arg1 - ser:<tty device>
            arg2 - <baudrate>-<databit>-<parity>-<timeout>-<stopbits>-<dsrdtr>-<xonxoff>-<rtscts>
        For tcp: create socket connection with specify parameters:
            arg1 - tcp:<scpi ip address>:<port>

    close
        For serial: close tty device with specify parameters: 
            arg1 - ser:<tty device>
        For tcp: close socket connection with specify parameters:
            arg1 - tcp:<scpi ip address>:<port>

    state
        For serial: get scpi device state with specify parameters: 
            arg1 - ser:<tty device>
        For tcp: get scpi device state with specify parameters:
            arg1 - tcp:<scpi ip address>:<port>

    send
        For serial: send scpi command string to scpi device and get response from scpi device with specify parameters: 
            arg1 - ser:<tty device>
            arg2 - <scpi device command string>
        For tcp: send scpi command string to scpi device and get response from scpi device with specify parameters:
            arg1 - tcp:<scpi ip address>:<port>
            args - <scpi device command string>

## Test

To run the plugin, add `pymodules/pyscpi` into `modules.conf` and restart all services.

## internals

