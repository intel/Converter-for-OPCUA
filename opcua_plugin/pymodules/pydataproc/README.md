# pydataproc 

## Description

pydataproc plugin enables on-the-fly data processing with user-defined Python function. It gets data from specified source location, process it and stores processed result into specified sink location.

## Language

Python

## Configuration

The following properties can be configured by editing `plugin_pydataproc.json`:

	source_topic
		specify source topic name. e.g. "source_test"
		
	sink_topic
		specify sink topic name. e.g. "sink_test"
		
	udf_enabled
		set if udf is enabled. e.g. "no"
		
	udf_file
		specify udf file name. eg. "udf_simple.py"

## OPC UA Methods

The plugin will provide following OPC UA methods:

	set_udf_file
		set udf file name

	set_udf_enabled
		enable / disable udf

## Test

A sample program is developed to show how to use pydataproc plugin. The UDF process function will filter out messages that `line` not equals 1 and only return line 1 messages. The original data is transformed and only return `timestamp` and `measurement` fields. 

The data file `measurement_data.jsonl` used in the sample is generated data based on a faked production line sensor measurements. `data-sim-amqp.py` is the simulator program to send data into AMQP source queue. `data-mon-amqp.py` is the monitor program to print out processed data from AMQP sink queue. The names of AMQP Source queue and AMQP Sink queue are `source_test` and `sink_test` respectively. `udf_simple.py` is the example UDF that do the real processing. Check `plugin_pydataproc.json` for detailed plugin configuration.

To run the plugin, add `pymodules/pydataproc` into `modules.conf` and restart all services.

Firstly run `data-mon-amqp.py` to generate data:

	$ python data-mon-amqp.py

And then run `data-sim-amqp.py` to check the processed data:

	$ python data-sim-amqp.py

## Internals

### Terminology


* AMQP: Advanced Message Queuing Protocol.
* UDF: User-defined Function
* UDF file: The .py file that defining UDF
* Client: The program invokes processing functions provided by pydataproc plugin

### Data Processing Flow

Client will send data to AMQP Source queue and pydataproc UDF will process data and send result to AMQP Sink queue.

The Data Flow is: 

	AMQP Source queue ==> pydataproc UDF ==> AMQP Sink queue

The processing logic is defined in UDF of specified Python .py file and invoked by pydataproc plugin

### Data Processing with UDF

UDF is defined in a specified .py file and with a special function named "process". There are some restrictions apply to this function:

* The UDF file is a syntax correct python file
* The UDF file should only import modules that in a module whitelist
* The function should be named "process" and only take one parameter which represent the data it will process.
	
The initial implementation will provide per-message only stateless operations:

* Data Filtering: UDF to return False to filter out current data transmission or True to allow data transmission
* Data Transformation: UDF return per-message transformed result data

### Raw Data Format

pydataproc uses JSON to represent data for both source data and processed data. Each message is a flat JSON object, and each field is a K-V pair. The data inside JSON message follow standard JSON value types: string, number, true, false, null. Don't define nested JSON structure for simplicity and easy to parse.

E.g. 

	{"idx": 1, "event_type": "NEW_MEASUREMENT", "ts": "2018-06-05 01:51:06.785207", "ts_gateway": "2018-06-05 01:51:07.785207", "product": 1, "line": 1, "station": 4, "measurement": 140}

### Source and Sink Locations

The Client can specify source and sink location by calling plugin provided APIs. The initial implementation for such location is defined with AMQP queues. The plugin will use default AMQP infrastructure provided for Converter for OPC UA. We may support more data locations in the future.
