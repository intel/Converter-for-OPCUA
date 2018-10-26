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

#ifndef _CONFIG_
#define _CONFIG_

#include "json.h"

typedef struct cfg_data {
	json_object *jobj;
	const char *topic_name;
	char data[8192];

} cfg_data_t;

int strcmp_ss(const char *dest, const char *src);
int memcmp_ss(const void *dest, const void *src, int len);
int memcpy_ss(void *dest, const void *src, int len);
cfg_data_t *cfg_loads(const char *filename);
json_object *seek_node(json_object *element, const char *key);
json_object *get_custom_nodes(void);

#endif
