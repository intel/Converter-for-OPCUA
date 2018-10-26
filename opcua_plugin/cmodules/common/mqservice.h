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

#ifndef _MQSERVICE_
#define _MQSERVICE_

#include "json_object.h"
#include <pthread.h>

typedef struct sema_ {
	pthread_mutex_t mutex;
	pthread_cond_t   cond;
	int v;
} sema;
void  sema_init(sema *sema_p, int value);
void  sema_post(sema *sema_p);
void  sema_wait(sema *sema_p);

int mqservice_start(char *host_name, int port, const char *routing);
void mqservice_stop(void);
int mqservice_publish(const char *remote_queue, const char *req_json);
char *mqservice_request(const char *remote_queue, const char *req_json);
void mqservice_setcallback(json_object * (*on_request)(json_object *jobj), void (*on_notify)(const char *));

#endif
