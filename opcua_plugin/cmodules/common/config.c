/*
* Copyright (c) 2017 Intel Corporation
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>	// for strerror
#include <safe_str_lib.h>
#include <safe_mem_lib.h>
#include <assert.h>
#include <locale.h>
#include <getopt.h>
#include "json.h"
#include "config.h"

static cfg_data_t plugin_data;
static void json_parse(json_object * jobj);
static void json_parse_array( json_object *jobj, char *key);

int strcmp_ss(const char *dest, const char *src)
{
	errno_t rc;
	int ind;
	rc = strcmp_s(dest, strnlen_s(dest,256), src, &ind);
	if(rc){
		printf("string compare failed");
		return -1;
	}else
		return ind;
}

int memcmp_ss(const void *dest, const void *src, int len)
{
	errno_t rc;
	int diff;
	rc = memcmp_s(dest, len, src, len, &diff);
	if(rc){
		printf("memory compare failed");
		return -1;
	}else
		return diff;
}

int memcpy_ss(void *dest, const void *src, int len)
{
	errno_t rc;
	rc = memcpy_s(dest, len + 1, src, len);
	if(rc){
		printf("memory compare failed");
		return -1;
	}else
		return len + 1;
}

static char *read_jsonstr(const char *filename)
{
	FILE *file = fopen(filename, "r");
	if (!file) {
		fprintf(stderr, "error: cannot open %s: %s", filename, strerror(errno));
		return NULL;
	}
	memset_s(plugin_data.data, 8192, 0);
	fread(plugin_data.data, 1, 8192, file);
	fclose(file);
	return plugin_data.data;
}

static void json_parse(json_object * jobj) {
	enum json_type type;
	json_object_object_foreach(jobj, key, val) {
		type = json_object_get_type(val);
		switch (type) {
			case json_type_boolean:
			case json_type_double:
			case json_type_int:
			case json_type_string: // print_json_value(val);
	                           break;
			case json_type_object: printf("json_type_objectn");
	                           jobj = json_object_object_get(jobj, key);
	                           json_parse(jobj);
	                           break;
			case json_type_array: printf("type: json_type_array, ");
	                          json_parse_array(jobj, key);
	                          break;
		}
	}
}

static void json_parse_array( json_object *jobj, char *key) {
	enum json_type type;
	int arraylen, i;
	json_object * jvalue;
	json_object *jarray = jobj;
	if(key) {
		jarray = json_object_object_get(jobj, key);
	}

	arraylen = json_object_array_length(jarray);
	printf("Array Length: %dn",arraylen);

	for (i=0; i< arraylen; i++) {
		jvalue = json_object_array_get_idx(jarray, i);
		type = json_object_get_type(jvalue);
		if (type == json_type_array) {
			json_parse_array(jvalue, NULL);
		} else if (type != json_type_object) {
			printf("value[%d]: ",i);
			// print_json_value(jvalue);
		} else {
			json_parse(jvalue);
		}
	}
}

json_object *seek_node(json_object *jobj, const char *node_key)
{
	enum json_type type;
	json_object_object_foreach(jobj, key, val) {
		if(strcmp_ss(key, node_key) == 0) {
			return json_object_object_get(jobj, key);
		}
	}
	return NULL;
}

cfg_data_t * cfg_loads(const char *filename)
{
	struct json_object *jobj;
	char *json_str = read_jsonstr(filename);
	jobj = json_tokener_parse(json_str);
	plugin_data.jobj = jobj;
	jobj = seek_node(jobj, "user_data");
	jobj = seek_node(jobj, "topic");
	plugin_data.topic_name = json_object_get_string(jobj);
	return &plugin_data;
}

json_object *get_custom_nodes()
{
	json_object *jobj, *jobj1, *jobj2, *jvalue, *getNode;
	json_object *getNodes = json_object_new_array();
	const char *jval = NULL;
	jobj = plugin_data.jobj;
	jobj = seek_node(jobj, "user_data");
	jobj = seek_node(jobj, "opcua");
	jobj1 = seek_node(jobj, "custom_types");

	// if jlen > 0 ?
	int jLen1 = json_object_array_length(jobj1);
	int i;
	for(i = 0; i < jLen1;i++)
	{
		jvalue = json_object_array_get_idx(jobj1, i);
		jvalue = seek_node(jvalue, "name");
		jval = json_object_get_string(jvalue);
	}

	jobj2 = seek_node(jobj, "folders");
	int jLen2 = json_object_array_length(jobj2);
	for(i = 0;i < jLen2; i++)
	{
		jvalue = json_object_array_get_idx(jobj2, i);
		json_object_object_foreach(jvalue, key, val) {
			if(NULL != jval) {
				if(strcmp_ss(key, jval) == 0) {
					getNode = json_object_object_get(jvalue, key);
					json_object_array_add(getNodes,getNode);
				}
			}
		}
	}
	return getNodes;
}

