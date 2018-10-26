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

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <safe_str_lib.h>
#include <stdarg.h>
#include <unistd.h>
#include <pthread.h>
#include "mqservice.h"
#include "json.h"
#include "config.h"
#include "client.h"

#define MQSERVICE_HOSTNAME "127.0.0.1"
#define MQSERVICE_PORT 5672

static pthread_t cli_thread;
static const char *cli_name = NULL;
static cfg_data_t *cli_cfgdata = NULL;
static int cli_stopflag = 0;

static void cli_main(void);
static json_object *getrd(json_object *data_obj);
static json_object *(*cli_plugin_call)(const char *method, json_object *data_obj) = NULL;

static cli_func_map func_map[] = {
	{ "getrd", getrd }
};

json_object *getrd(json_object *data_obj)
{
	json_object *result_obj = json_object_new_object();
	const char *data = json_object_to_json_string_ext(cli_cfgdata->jobj, JSON_C_TO_STRING_PLAIN); 
	json_object_object_add(result_obj, "code", 0);
	json_object_object_add(result_obj, "data", json_object_new_string(data));
	return result_obj;
}

json_object *cli_call(const char *method, json_object *data_obj)
{
	int i;
	for (i = 0; i < (sizeof(func_map) / sizeof(func_map[0])); i++) {
	    if (!strcmp_ss(func_map[i].name, method) && func_map[i].func) {
	      return func_map[i].func(data_obj);
	    }
  	}
	if (NULL != cli_plugin_call) {
		return cli_plugin_call(method, data_obj);
	}
	return NULL;
}

static json_object* _on_receive(json_object *jobj)
{
	const char *method = json_object_get_string(seek_node(jobj, "method"));
	json_object *data_obj = seek_node(jobj, "data");
	return cli_call(method, data_obj);
}

static void _on_notify(const char *json_str)
{
	printf("%s\n", json_str);
}

void cli_start(cfg_data_t *cfgdata)
{
	const char *pos = NULL;
	if((NULL == cfgdata) || (NULL == cfgdata->topic_name))
		return;
	pos = cfgdata->topic_name;
	while (*pos)
    {
        if ('/' == *pos)
        {
        	pos++;
            break;
        }
        pos++;
    }
	if(0 == strnlen_s(pos, 256))
		return;
	cli_name = pos;
	cli_cfgdata = cfgdata;
	pthread_create(&cli_thread, NULL, (void*)cli_main, NULL);

	mqservice_setcallback(_on_receive, _on_notify);
	mqservice_start(MQSERVICE_HOSTNAME, MQSERVICE_PORT, cli_name);
}

void cli_setcallback(json_object * (*plugin_call)(const char *, json_object *))
{
	cli_plugin_call = plugin_call;
}

void cli_stop(void)
{
	cli_stopflag = 1;
	mqservice_stop();
	pthread_join(cli_thread,NULL);
}

int cli_pub_data(const char *dev_name, const char *var_name, json_object* var_obj)
{
	const char *json_str = NULL;
	json_object * jobj = json_object_new_object();
	json_object *jarray = json_object_new_array();
	json_object *jstring0= json_object_new_string(cli_name);
	json_object *jstring1 = json_object_new_string(dev_name);
	json_object *jstring2 = json_object_new_string(var_name);
	json_object_array_add(jarray,jstring0);
	json_object_array_add(jarray,jstring1);
	json_object_array_add(jarray,jstring2);
	json_object_array_add(jarray,var_obj);
	json_object_object_add(jobj,"data", jarray);
	json_str = json_object_to_json_string_ext(jobj, JSON_C_TO_STRING_PLAIN);
	int retcode = mqservice_publish("opcua", json_str);
	json_object_put(jobj);
    return retcode;
}

int cli_pub_event(const char *dev_name, const char *evt_name, const char *evt_data)
{
	const char *json_str = NULL;
	json_object * jobj = json_object_new_object();
	json_object *jarray = json_object_new_array();
	json_object *jstring0= json_object_new_string(cli_name);
	json_object *jstring1 = json_object_new_string(dev_name);
	json_object *jstring2 = json_object_new_string(evt_name);
	json_object *jstring3 = json_object_new_string(evt_data);
	json_object_array_add(jarray, jstring0);
	json_object_array_add(jarray, jstring1);
	json_object_array_add(jarray, jstring2);
	json_object_array_add(jarray, jstring3);
	json_object_object_add(jobj, "event", jarray);

	json_str = json_object_to_json_string_ext(jobj, JSON_C_TO_STRING_PLAIN);
	int retcode = mqservice_publish("opcua", json_str);
	json_object_put(jobj);
    return retcode;
}

void cli_main(void)
{
	int retcode;
  
	sleep(1);
  
	while(!cli_stopflag) {	
		retcode = cli_pub_event("", "online", "");		
		if (retcode < 0)
		{
			exit(-1);
		}

		sleep(3);
	}
}

