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
#include <stdarg.h>
#include <safe_mem_lib.h>
#include <amqp.h>
#include <amqp_tcp_socket.h>
#include <sys/time.h>
#include "mqservice.h"
#include "json.h"
#include "config.h"

#define MQSERVICE_VHOST "/"
#define MQSERVICE_MAX_CHANNEL 65535
#define MQSERVICE_FRAME_MAX 131072
#define MQSERVICE_HEART_BEAT 60

static sema mq_reqsem;
static pthread_t mq_thread;
static json_object *(*mq_on_request)(json_object *jobj) = NULL;
static void (*mq_on_notify)(const char *message) = NULL;
static amqp_connection_state_t mq_conn = 0;
static amqp_bytes_t mq_replyqueue = {0, NULL};
static amqp_bytes_t mq_respbytes = {0, NULL};
static char mq_requuid[37];

void sema_init(sema *sema_p, int value) {
	if (value < 0 || value > 1) {
		printf("bsem_init(): Binary semaphore can take only values 1 or 0");
		exit(1);
	}
	pthread_mutex_init(&(sema_p->mutex), NULL);
	pthread_cond_init(&(sema_p->cond), NULL);
	sema_p->v = value;
}

void sema_post(sema *sema_p) {
	pthread_mutex_lock(&sema_p->mutex);
	sema_p->v = 1;
	pthread_cond_signal(&sema_p->cond);
	pthread_mutex_unlock(&sema_p->mutex);
}

void sema_wait(sema *sema_p) {
	pthread_mutex_lock(&sema_p->mutex);
	while (sema_p->v != 1) {
		pthread_cond_wait(&sema_p->cond, &sema_p->mutex);
	}
	sema_p->v = 0;
	pthread_mutex_unlock(&sema_p->mutex);
}

static int amqp_check_error(amqp_rpc_reply_t reply, char const *context) {
  switch (reply.reply_type) {
    case AMQP_RESPONSE_NORMAL:
      return 0;

    case AMQP_RESPONSE_NONE:
      fprintf(stderr, "%s: type!\n", context);
      break;

    case AMQP_RESPONSE_LIBRARY_EXCEPTION:
      fprintf(stderr, "%s: exception %s\n", context, amqp_error_string2(reply.library_error));
      break;

    case AMQP_RESPONSE_SERVER_EXCEPTION:
      switch (reply.reply.id) {
        case AMQP_CONNECTION_CLOSE_METHOD: {
          amqp_connection_close_t *msg =
              (amqp_connection_close_t *)reply.reply.decoded;
          fprintf(stderr, "%s: error %uh, message: %.*s\n",
                  context, msg->reply_code, (int)(msg->reply_text.len),
                  (char *)(msg->reply_text.bytes));
          break;
        }
        case AMQP_CHANNEL_CLOSE_METHOD: {
          amqp_channel_close_t *msg = (amqp_channel_close_t *)reply.reply.decoded;
          fprintf(stderr, "%s: error %uh, message: %.*s\n",
                  context, msg->reply_code, (int)(msg->reply_text.len),
                  (char *)(msg->reply_text.bytes));
          break;
        }
        default:
          fprintf(stderr, "%s: unknown error, 0x%X\n",
                  context, reply.reply.id);
          break;
      }
      break;
  }

  return -1;
}

static void amqp_task(char *param){
	for (;;) {
	    amqp_rpc_reply_t res;
	    amqp_envelope_t envelope;
		amqp_message_t message;

	    amqp_maybe_release_buffers(mq_conn);

	    res = amqp_consume_message(mq_conn, &envelope, NULL, 0);

	    if (AMQP_RESPONSE_NORMAL != res.reply_type) {
	      break;
	    }

		message = envelope.message;
		if(message.properties.reply_to.bytes == NULL) {
			if(memcmp_ss(mq_replyqueue.bytes,envelope.routing_key.bytes,mq_replyqueue.len) == 0) {
				if(memcmp_ss(mq_requuid, envelope.message.properties.correlation_id.bytes, 32) == 0) {
					mq_respbytes = amqp_bytes_malloc_dup(message.body);
					sema_post(&mq_reqsem);
				}
			} else if(mq_on_notify) {
				mq_on_notify((char *)message.body.bytes);
			}
		} else {
			printf("on request\n"); //message.body.bytes, envelope.message.body.len

			amqp_basic_ack(mq_conn, 1, envelope.delivery_tag, 0);
			amqp_basic_properties_t props;
			props._flags = AMQP_BASIC_CONTENT_TYPE_FLAG | AMQP_BASIC_CORRELATION_ID_FLAG;
			props.content_type = amqp_cstring_bytes("text/plain");
			printf("%s\n",(char *)(message.properties.correlation_id.bytes));
			props.correlation_id = message.properties.correlation_id;

			json_object *json_in = NULL;
			json_object *json_out = NULL;
			char *token_str = NULL;
			if(message.body.len > 0) {
				token_str = (char *)malloc(message.body.len + 1);
				if(NULL != token_str) {
					memcpy_ss(token_str, message.body.bytes, message.body.len);
					token_str[message.body.len] = 0;
					json_in = json_tokener_parse((char *)token_str);
					if(mq_on_request) {
						json_out = mq_on_request(json_in);
					}
					free(token_str);
				}
			}
			const char *req_result = NULL;
			if(json_out)
			    req_result = json_object_to_json_string_ext(json_out, JSON_C_TO_STRING_PLAIN);
			printf("# # %s\n", (char *)(message.properties.reply_to.bytes));
			amqp_basic_publish(mq_conn, 1, amqp_cstring_bytes(""),
									message.properties.reply_to, 0, 0,
									&props, amqp_cstring_bytes(req_result));
			json_object_put(json_in);
			json_object_put(json_out);
		}
		amqp_destroy_envelope(&envelope);
	}
}

int mqservice_start(char* hostname, int port, const char *routing)
{
	int status;
	amqp_socket_t *socket = NULL;
	amqp_connection_state_t conn;
	amqp_rpc_reply_t result;

	conn = amqp_new_connection();

	socket = amqp_tcp_socket_new(conn);
	if (!socket) {
		printf("creating TCP socket fail");
      	return -1;
	}

	status = amqp_socket_open(socket, hostname, port);
	if (status) {
		printf("opening TCP socket fail");
      	return status;
	}
  
  	amqp_login(conn, MQSERVICE_VHOST, MQSERVICE_MAX_CHANNEL, MQSERVICE_FRAME_MAX, MQSERVICE_HEART_BEAT, AMQP_SASL_METHOD_PLAIN,
							   "guest", "guest");
	amqp_channel_open(conn, 1);
	status = amqp_check_error(amqp_get_rpc_reply(conn), "Open channel");
	if(status)
		return status;

	amqp_queue_declare_ok_t *r = amqp_queue_declare(
		conn, 1, amqp_empty_bytes, 0, 0, 1, 1, amqp_empty_table);
	status = amqp_check_error(amqp_get_rpc_reply(conn), "Declare queue");
	if(status)
		return status;

	mq_replyqueue = amqp_bytes_malloc_dup(r->queue);
	if (mq_replyqueue.bytes == NULL) {
	  	fprintf(stderr, "Out of memory while copying queue name");
	  	return -1;
	}

	amqp_basic_consume(conn, 1, mq_replyqueue, amqp_empty_bytes,
					 0, 0, 0, amqp_empty_table);
	status = amqp_check_error(amqp_get_rpc_reply(conn), "Consume");
	if(status)
		return status;

	amqp_queue_declare(
		conn, 1, amqp_cstring_bytes(routing), 0, 0, 0, 0, amqp_empty_table);
	status = amqp_check_error(amqp_get_rpc_reply(conn), "Declare queue");
	if(status)
		return status;

	amqp_basic_consume(conn, 1, amqp_cstring_bytes(routing), amqp_empty_bytes,
					 0, 0, 0, amqp_empty_table);
	status = amqp_check_error(amqp_get_rpc_reply(conn), "Consume");
	if(status)
		return status;

	pthread_create(&mq_thread,NULL,(void*)amqp_task,NULL);

	amqp_basic_properties_t props;
	props.content_type = amqp_cstring_bytes("application/json");

	mq_conn = conn;
	sema_init(&mq_reqsem, 0);

	return 0;
}

void mqservice_stop(void)
{
 	amqp_channel_close(mq_conn, 1, AMQP_REPLY_SUCCESS);
	amqp_connection_close(mq_conn, AMQP_REPLY_SUCCESS);
	amqp_destroy_connection(mq_conn);
	pthread_join(mq_thread,NULL);
}

int mqservice_publish(const char *remote_queue, const char *req_json)
{
	amqp_basic_properties_t props;
	props._flags = AMQP_BASIC_CONTENT_TYPE_FLAG | AMQP_BASIC_DELIVERY_MODE_FLAG;
	props.content_type = amqp_cstring_bytes("application/json");
	props.delivery_mode = 2; /* persistent delivery mode */
	int retcode = amqp_basic_publish(mq_conn, 1, amqp_cstring_bytes(""),
								amqp_cstring_bytes(remote_queue), 0, 0,
								&props, amqp_cstring_bytes(req_json));
	return retcode;
}

static void uuid_generate_lower(char* requuid, int len) {
	const char alphabet[] = "abcdefghijklmnopqrstuvwxyz0123456789";
	struct timeval t;
	int i = 0;
	gettimeofday(&t, NULL);
	srand(t.tv_usec);
	for (i = 0; i < len - 1; i++) {
		requuid[i] = alphabet[rand()%36];
	}
	requuid[len] = '\0';
}

char *mqservice_request(const char *remote_queue, const char *req_json)
{
	int status;
	amqp_basic_properties_t props;
	props._flags = AMQP_BASIC_CONTENT_TYPE_FLAG |
				  AMQP_BASIC_REPLY_TO_FLAG |
				  AMQP_BASIC_CORRELATION_ID_FLAG;
	props.content_type = amqp_cstring_bytes("application/json");
	props.reply_to = amqp_bytes_malloc_dup(mq_replyqueue);
	if (props.reply_to.bytes == NULL) {
		fprintf(stderr, "Out of memory while copying queue name");
		return NULL;
	}

	uuid_generate_lower(mq_requuid, sizeof(mq_requuid) - 1);
	props.correlation_id = amqp_cstring_bytes(mq_requuid);
	amqp_basic_publish(mq_conn, 1, amqp_cstring_bytes(""),
								   amqp_cstring_bytes(remote_queue), 0, 0,
								   &props, amqp_cstring_bytes(req_json));

	amqp_bytes_free(props.reply_to);
	sema_wait(&mq_reqsem);
	return mq_respbytes.bytes;
}

void mqservice_setcallback(json_object * (*on_request)(json_object *), void (*on_notify)(const char *))
{
	mq_on_request = on_request;
	mq_on_notify = on_notify;
}

