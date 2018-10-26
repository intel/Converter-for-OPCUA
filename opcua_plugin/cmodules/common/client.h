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

#ifndef _CLIENT_
#define _CLIENT_

#include "config.h"

typedef struct {
	const char *name;
	json_object *(*func)(json_object *data_obj);
} cli_func_map;

void cli_start(cfg_data_t *cfgdata);
void cli_stop(void);
int cli_pub_data(const char *dev_name, const char *var_name, json_object* var_obj);
int cli_pub_event(const char *dev_name, const char *evt_name, const char *evt_data);
void cli_setcallback(json_object * (*plugin_call)(const char *, json_object *));

#endif
