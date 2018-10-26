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
#include "config.h"
#include "client.h"
#include <errno.h>
#include <unistd.h>
#include "json_object.h"
#include <modbus/modbus.h>
#include <safe_mem_lib.h>

#define MAX_MB_TABLE_SIZE 	(256)
#define MAX_MB_RANGE_OFFSET (1024)
typedef struct _mbclient_t {
  const char	*name;
  const char	*address;
  int 	baudrate;
  int 	period;
  int 	server_id;
  uint16_t valid_coils[MAX_MB_TABLE_SIZE];
  uint16_t valid_coils_num;
  const char	*coils_refs;
  uint16_t valid_inputs[MAX_MB_TABLE_SIZE];
  uint16_t valid_inputs_num;
  const char	*inputs_refs;
  uint16_t valid_hregs[MAX_MB_TABLE_SIZE];
  uint16_t valid_hregs_num;
  const char	*hregs_refs;
  uint16_t valid_iregs[MAX_MB_TABLE_SIZE];
  uint16_t valid_iregs_num;
  const char	*iregs_refs;
  modbus_t *ctx;
  uint8_t      predefined;
}mbclient_t;

static mbclient_t *mbclients = NULL;
static int mbclients_count = 0;
static int stopflag = 0;

static json_object *connect(json_object *data_obj);
static json_object *disconnect(json_object *data_obj);
static json_object *write_coil(json_object *data_obj);
static json_object *write_register(json_object *data_obj);
static json_object *read_coils(json_object *data_obj);
static json_object *read_discrete_inputs(json_object *data_obj);
static json_object *read_holding_registers(json_object *data_obj);
static json_object *read_input_registers(json_object *data_obj);

static cli_func_map modbus_func_map[] = {
	{ "connect", connect },
	{ "disconnect", disconnect },
	{ "write_coil", write_coil},
	{ "read_coils", read_coils},
	{ "read_discrete_inputs", read_discrete_inputs},
	{ "write_register", write_register},
	{ "read_holding_registers", read_holding_registers},
	{ "read_input_registers", read_input_registers}
};

enum MBDataType
{
	COILS,DISCRETE_INPUTS,HOLDING_REGS,INPUT_REGS
};

static json_object *plugin_call(const char *method, json_object *data_obj)
{
	int i;
	for (i = 0; i < (sizeof(modbus_func_map) / sizeof(modbus_func_map[0])); i++) {
	    if (!strcmp_ss(modbus_func_map[i].name, method) && modbus_func_map[i].func) {
	      return modbus_func_map[i].func(data_obj);
	    }
	}
	return NULL;
}

static json_object *json_result(int error_code, const char *data)
{
	json_object *result_obj = json_object_new_object();
	json_object_object_add(result_obj, "code", json_object_new_int(error_code));
	json_object_object_add(result_obj, "data", json_object_new_string(data));
	return result_obj;
}

static json_object *json_result_obj(int error_code, json_object *data_obj)
{
	json_object *result_obj = json_object_new_object();
	const char *data = json_object_to_json_string_ext(data_obj, JSON_C_TO_STRING_PLAIN); 
	json_object_object_add(result_obj, "code", json_object_new_int(error_code));
	json_object_object_add(result_obj, "data", json_object_new_string(data));
	return result_obj;
}

static json_object *connect(json_object *data_obj)
{
	const char *address = NULL;
	int baudrate = 115200;
	int server_id = 17;
	json_object *param0 = json_object_array_get_idx(data_obj, 0);
	address = json_object_get_string(param0);
	if(json_object_array_length(data_obj) > 1) {
		json_object *param1 = json_object_array_get_idx(data_obj, 1);
		baudrate = atoi(json_object_get_string(param1));
	}
	if(json_object_array_length(data_obj) > 2) {
		json_object *param2 = json_object_array_get_idx(data_obj, 2);
		server_id = atoi(json_object_get_string(param2));
	}
	mbclient_t *client = NULL;
	if(NULL == address ) {
		return json_result(-1, "Modbus plugin parameter error");
	}
	int i;
	for(i = 0; i < mbclients_count; i++) {
		if(0 == strcmp_ss(mbclients[i].address, address)){
			client = &(mbclients[i]);
			break;
		}
	}
	if(NULL == client) {
		mbclients = realloc(mbclients, sizeof(mbclient_t) * (mbclients_count + 1));
		if(NULL == mbclients) {
			return json_result(-1, "Modbus plugin memory error");
		}
		client = &(mbclients[mbclients_count]);
		mbclients_count += 1;
	}
	if(NULL == client->ctx){
		client->address = address;
		client->baudrate = baudrate;
		client->server_id = server_id;
		client->period = 0;
		if(client->baudrate > 0 && client->address) {
			//modbus_t *ctx = modbus_new_rtu(client->address, client->baudrate, 'N', 8, 1);
			modbus_t *ctx = modbus_new_rtu(address, baudrate, 'N', 8, 1);
			if (ctx == NULL) {
				fprintf(stderr, "Unable to allocate libmodbus context\n");
				return json_result(-1, "Modbus plugin allocate error");
			} else {
				modbus_set_slave(ctx, client->server_id);
				modbus_set_debug(ctx, TRUE);
				modbus_set_error_recovery(ctx,
											  MODBUS_ERROR_RECOVERY_LINK |
											  MODBUS_ERROR_RECOVERY_PROTOCOL);
				if (modbus_connect(ctx) == -1) {
					fprintf(stderr, "Connection failed: %s\n", modbus_strerror(errno));
					modbus_free(ctx);
					ctx = NULL;
					return json_result(-1, "Modbus plugin connect error");
				} else {
					client->ctx = ctx;
					client->predefined = FALSE;
				}
			}
		}
	}
	return json_result(0, "SUCCESS");
}

static json_object *disconnect(json_object *data_obj)
{
	const char *address = NULL;
	json_object *param0 = json_object_array_get_idx(data_obj, 0);
	address = json_object_get_string(param0);
	mbclient_t *client = NULL;
	if(NULL == address ) {
		return json_result(-1, "Modbus plugin parameter error");
	}
	int i;
	for(i = 0; i < mbclients_count; i++) {
		printf("disconnect %s %s\n", mbclients[i].address, address);
		if(0 == strcmp_ss(mbclients[i].address, address)){
			client = &(mbclients[i]);
			break;
		}
	}
	if(NULL == client || NULL == client->ctx) {
		return json_result(-1, "Modbus plugin not connected");
	}
	if(TRUE == client->predefined){
		return json_result(-1, "disconnect not allow");
	}
	modbus_close(client->ctx);
	modbus_free(client->ctx);
	client->ctx = NULL;
	return json_result(0, "SUCCESS");
}

static json_object *read_coils(json_object *data_obj)
{
	const char *address = NULL;
	int coils_num = 0;
	int offset, rr;
	if(json_object_array_length(data_obj) > 2){
		json_object *param0 = json_object_array_get_idx(data_obj, 0);
		address = json_object_get_string(param0);
		json_object *param1 = json_object_array_get_idx(data_obj, 1);
		offset = atoi(json_object_get_string(param1));
		json_object *param2 = json_object_array_get_idx(data_obj, 2);
		coils_num = atoi(json_object_get_string(param2));
		if(coils_num <= 0 || coils_num > MAX_MB_RANGE_OFFSET) {
			return json_result(-1, "Modbus plugin parameter error");
		}
	}
	if(NULL == address || 0 == coils_num) {
		return json_result(-1, "Modbus plugin parameter error");
	}
	mbclient_t *client = NULL;
	int i;
	for(i = 0; i < mbclients_count; i++) {
		if(0 == strcmp_ss(mbclients[i].address, address)){
			client = &(mbclients[i]);
			break;
		}
	}
	if(NULL == client || NULL == client->ctx) {
		return json_result(-1, "read coils not found");
	}

	uint8_t dest[coils_num];
	rr = modbus_read_bits(client->ctx,offset - 1, coils_num, dest);
	if(rr == -1){
		return json_result(-1, "data error");
	}

	json_object *jarray = json_object_new_array();
	int j;
	for(j = 0; j< coils_num; j++) {
		json_object *jint= json_object_new_int(dest[j]);
		json_object_array_add(jarray,jint);
	}
	return json_result_obj(0, jarray);
}

static json_object *read_discrete_inputs(json_object *data_obj)
{
	const char *address = NULL;
	int discrete_num = 0;
	int offset, rr;
	if(json_object_array_length(data_obj) > 2){
		json_object *param0 = json_object_array_get_idx(data_obj, 0);
		address = json_object_get_string(param0);
		json_object *param1 = json_object_array_get_idx(data_obj, 1);
		offset = atoi(json_object_get_string(param1));
		json_object *param2 = json_object_array_get_idx(data_obj, 2);
		discrete_num = atoi(json_object_get_string(param2));
		if(discrete_num <= 0 || discrete_num > MAX_MB_RANGE_OFFSET) {
			return json_result(-1, "Modbus plugin parameter error");
		}
	}
	if(NULL == address || 0 == discrete_num) {
		return json_result(-1, "Modbus plugin parameter error");
	}
	mbclient_t *client = NULL;
	int i;
	for(i = 0; i < mbclients_count; i++) {
		if(0 == strcmp_ss(mbclients[i].address, address)){
			client = &(mbclients[i]);
			break;
		}
	}
	if(NULL == client || NULL == client->ctx) {
		return json_result(-1, "discrete inputs not found");
	}

	uint8_t dest[discrete_num];
	rr = modbus_read_input_bits(client->ctx,offset - 1, discrete_num, dest);
	if(rr == -1){
		return json_result(-1, "data error");
	}

	json_object *jarray = json_object_new_array();
	int j;
	for(j = 0; j< discrete_num; j++) {
		json_object *jint= json_object_new_int(dest[j]);
		json_object_array_add(jarray,jint);
	}
	return json_result_obj(0, jarray);
}

static json_object *read_holding_registers(json_object *data_obj)
{
	const char *address = NULL;
	int hreg_num = 0;
	int offset, rr;
	if(json_object_array_length(data_obj) > 2){
		json_object *param0 = json_object_array_get_idx(data_obj, 0);
		address = json_object_get_string(param0);
		json_object *param1 = json_object_array_get_idx(data_obj, 1);
		offset = atoi(json_object_get_string(param1));
		json_object *param2 = json_object_array_get_idx(data_obj, 2);
		hreg_num = atoi(json_object_get_string(param2));
		if(hreg_num <= 0 || hreg_num > MAX_MB_RANGE_OFFSET) {
			return json_result(-1, "Modbus plugin parameter error");
		}
	}
	if(NULL == address || 0 == hreg_num) {
		return json_result(-1, "Modbus plugin parameter error");
	}
	mbclient_t *client = NULL;
	int i;
	for(i = 0; i < mbclients_count; i++) {
		if(0 == strcmp_ss(mbclients[i].address, address)){
			client = &(mbclients[i]);
			break;
		}
	}
	if(NULL == client || NULL == client->ctx) {
		return json_result(-1, "holding registers not found");
	}

	uint16_t dest[hreg_num];
	rr = modbus_read_registers(client->ctx,offset - 1, hreg_num, dest);
	if(rr == -1){
		return json_result(-1, "data error");
	}

	json_object *jarray = json_object_new_array();
	int j;
	for(j = 0; j< hreg_num; j++) {
		json_object *jint= json_object_new_int(dest[j]);
		json_object_array_add(jarray,jint);
	}
	return json_result_obj(0, jarray);
}

static json_object *read_input_registers(json_object *data_obj)
{
	const char *address = NULL;
	int ireg_num = 0;
	int offset, rr;
	if(json_object_array_length(data_obj) > 2){
		json_object *param0 = json_object_array_get_idx(data_obj, 0);
		address = json_object_get_string(param0);
		json_object *param1 = json_object_array_get_idx(data_obj, 1);
		offset = atoi(json_object_get_string(param1));
		json_object *param2 = json_object_array_get_idx(data_obj, 2);
		ireg_num = atoi(json_object_get_string(param2));
		if(ireg_num <= 0 || ireg_num > MAX_MB_RANGE_OFFSET) {
			return json_result(-1, "Modbus plugin parameter error");
		}
	}
	if(NULL == address || 0 == ireg_num) {
		return json_result(-1, "Modbus plugin parameter error");
	}
	mbclient_t *client = NULL;
	int i;
	for(i = 0; i < mbclients_count; i++) {
		if(0 == strcmp_ss(mbclients[i].address, address)){
			client = &(mbclients[i]);
			break;
		}
	}
	if(NULL == client || NULL == client->ctx) {
		return json_result(-1, "input registers not found");
	}

	uint16_t dest[ireg_num];
	rr = modbus_read_input_registers(client->ctx,offset - 1, ireg_num, dest);
	if(rr == -1){
		return json_result(-1, "data error");
	}

	json_object *jarray = json_object_new_array();
	int j;
	for(j = 0; j< ireg_num; j++) {
		json_object *jint= json_object_new_int(dest[j]);
		json_object_array_add(jarray,jint);
	}
	return json_result_obj(0, jarray);
}

static json_object *write_coil(json_object *data_obj){
	const char *address = NULL;
	int addr, value, rr;
	if(json_object_array_length(data_obj) > 2){
		json_object *param0 = json_object_array_get_idx(data_obj, 0);
		address = json_object_get_string(param0);
		json_object *param1 = json_object_array_get_idx(data_obj, 1);
		addr = atoi(json_object_get_string(param1));
		json_object *param2 = json_object_array_get_idx(data_obj, 2);
		value = atoi(json_object_get_string(param2));
	}
	if(NULL == address ) {
		return json_result(-1, "Modbus plugin parameter error");
	}
	mbclient_t *client = NULL;
	int i;
	for(i = 0; i < mbclients_count; i++) {
		if(0 == strcmp_ss(mbclients[i].address, address)){
			client = &(mbclients[i]);
			break;
		}
	}
	if(NULL == client || NULL == client->ctx) {
		return json_result(-1, "write coils not found");
	}

	rr = modbus_write_bit(client->ctx,addr - 1,value);
	if(rr == -1){
		return json_result(-1, "data error");
	}
	return json_result(0, "SUCCESS");
}

static json_object *write_register(json_object *data_obj){
	const char *address = NULL;
	int addr, value, rr;
	if(json_object_array_length(data_obj) > 2){
		json_object *param0 = json_object_array_get_idx(data_obj, 0);
		address = json_object_get_string(param0);
		json_object *param1 = json_object_array_get_idx(data_obj, 1);
		addr = atoi(json_object_get_string(param1));
		json_object *param2 = json_object_array_get_idx(data_obj, 2);
		value = atoi(json_object_get_string(param2));
	}
	if(NULL == address ) {
		return json_result(-1, "Modbus plugin parameter error");
	}
	mbclient_t *client = NULL;
	int i;
	for(i = 0; i < mbclients_count; i++) {
		if(0 == strcmp_ss(mbclients[i].address, address)){
			client = &(mbclients[i]);
			break;
		}
	}
	if(NULL == client || NULL == client->ctx) {
		return json_result(-1, "write register not found");
	}

	rr = modbus_write_register(client->ctx,addr - 1,value);
	if(rr == -1){
		return json_result(-1, "data error");
	}
	return json_result(0, "SUCCESS");
}

static uint8_t *read_inputs(modbus_t *ctx, uint16_t *valid_inputs, uint16_t inputs_num, enum MBDataType datatype)
{
	int offset, rr;
	uint8_t dest = 0;
	uint8_t* inputs_bits = NULL;
	if(inputs_num > 0)
		inputs_bits = malloc(inputs_num);

	if(NULL == inputs_bits)
		return NULL;

	for(offset = 0; offset < inputs_num; offset++)
	{
		if(datatype == DISCRETE_INPUTS)
			rr = modbus_read_input_bits(ctx, valid_inputs[offset] - 1, 1, &dest);
		else
			rr = modbus_read_bits(ctx,valid_inputs[offset] - 1, 1, &dest);
		if(rr)
			inputs_bits[offset] = dest;
		else
			inputs_bits[offset] = 0xFF;
	}
	return inputs_bits;
}

static uint16_t *read_registers(modbus_t *ctx, uint16_t *valid_regs, uint16_t regs_num, enum MBDataType datatype)
{
	int offset, rr;
	uint16_t dest = 0;
	uint16_t* inputs_regs = NULL;
	if(regs_num > 0)
		inputs_regs = malloc(regs_num * sizeof(uint16_t));

	if(NULL == inputs_regs)
		return NULL;

	for(offset = 0; offset < regs_num; offset++)
	{
		if(datatype == HOLDING_REGS)
			rr = modbus_read_registers(ctx, valid_regs[offset] - 1, 1, &dest);
		else
			rr = modbus_read_input_registers(ctx, valid_regs[offset] - 1, 1, &dest);
		if(rr)
			inputs_regs[offset] = dest;
		else
			inputs_regs[offset] = 0xFFFF;
	}
	return inputs_regs;
}

static void thread_loop(void)
{
	int now = 0;
	while(!stopflag)
	{
	    int i, j;
		for(i = 0 ;i < mbclients_count; i++) {
			uint8_t* inputs_bits;
			uint16_t* inputs_regs;
			if (mbclients[i].period == 0)
                    continue;
            if ((now % mbclients[i].period) == 0) {
				inputs_bits = read_inputs(mbclients[i].ctx, mbclients[i].valid_coils, mbclients[i].valid_coils_num, COILS);
				if(NULL != inputs_bits) {
					json_object *jarray = json_object_new_array();
					for(j = 0; j< mbclients[i].valid_coils_num; j++) {
						json_object *jint= json_object_new_int(inputs_bits[j]);
						json_object_array_add(jarray,jint);
					}
					cli_pub_data(mbclients[i].name, mbclients[i].coils_refs, jarray);
					free(inputs_bits);
					inputs_bits = NULL;
				}
				inputs_bits = read_inputs(mbclients[i].ctx, mbclients[i].valid_inputs, mbclients[i].valid_inputs_num, DISCRETE_INPUTS);
				if(NULL != inputs_bits) {
					json_object *jarray = json_object_new_array();
					for(j =0; j< mbclients[i].valid_inputs_num; j++) {
						json_object *jint= json_object_new_int(inputs_bits[j]);
						json_object_array_add(jarray,jint);
					}
					cli_pub_data(mbclients[i].name, mbclients[i].inputs_refs, jarray);
					free(inputs_bits);
					inputs_bits = NULL;
				}
				inputs_regs = read_registers(mbclients[i].ctx, mbclients[i].valid_hregs, mbclients[i].valid_hregs_num, HOLDING_REGS);
				if(NULL != inputs_regs) {
					json_object *jarray = json_object_new_array();
					for(j =0; j< mbclients[i].valid_hregs_num; j++) {
						json_object *jint= json_object_new_int(inputs_regs[j]);
						json_object_array_add(jarray,jint);
					}
					cli_pub_data(mbclients[i].name, mbclients[i].hregs_refs, jarray);
					free(inputs_regs);
					inputs_regs = NULL;
				}
				inputs_regs = read_registers(mbclients[i].ctx, mbclients[i].valid_iregs, mbclients[i].valid_iregs_num, INPUT_REGS);
				if(NULL != inputs_regs) {
					json_object *jarray = json_object_new_array();
					for(j =0; j < mbclients[i].valid_iregs_num; j++) {
						json_object *jint= json_object_new_int(inputs_regs[j]);
						json_object_array_add(jarray,jint);
					}
					cli_pub_data(mbclients[i].name, mbclients[i].iregs_refs, jarray);
					free(inputs_regs);
					inputs_regs = NULL;
				}
			}
		}

		now++;
		sleep(1);
	}
}

static void plugin_start()
{
	int i, j, k, l;
	json_object *folders = get_custom_nodes();
	int folders_count = json_object_array_length(folders);
	
	if (folders_count > 0) {
		json_object *clients = json_object_array_get_idx(folders, 0);
		int clients_count = json_object_array_length(clients);
		mbclients_count = clients_count;
		mbclients = malloc(sizeof(mbclient_t) * mbclients_count);
		if (NULL == mbclients) {
			fprintf(stderr, "memory allocat failed\n");
			return;
		}
		memset_s(mbclients, sizeof(mbclient_t) * mbclients_count, 0);

		for(j = 0; j < clients_count; j++) {
			mbclient_t *client = &(mbclients[j]);
			json_object *infos = json_object_array_get_idx(clients, j);
			json_object_object_foreach(infos, key, val) {
				if(strcmp_ss(key, "name") == 0) {
					client->name = json_object_get_string(val);
				} else if(strcmp_ss(key, "properties") == 0) {
					json_object *props = json_object_object_get(infos, key);
					int props_count = json_object_array_length(props);
					for(k = 0;k < props_count; k++)
					{
						json_object *prop = json_object_array_get_idx(props, k);
						json_object_object_foreach(prop, key, val) {
							if(strcmp_ss(key, "name") == 0) {
								json_object *value, *refs, *valids;
								if(strcmp_ss(json_object_get_string(val), "device address") == 0) {
									value = json_object_object_get(prop, "value");
									client->address = json_object_get_string(value);
								} else if(strcmp_ss(json_object_get_string(val), "baudrate") == 0) {
									value = json_object_object_get(prop, "value");
									client->baudrate = json_object_get_int(value);
								} else if(strcmp_ss(json_object_get_string(val), "period") == 0) {
									value = json_object_object_get(prop, "value");
									client->period = json_object_get_int(value);
								} else if(strcmp_ss(json_object_get_string(val), "server id") == 0) {
									value = json_object_object_get(prop, "value");
									client->server_id = json_object_get_int(value);
								} else if(strcmp_ss(json_object_get_string(val), "valid coils") == 0) {
									refs = json_object_object_get(prop, "refs");
									client->coils_refs = json_object_get_string(refs);
									value = json_object_object_get(prop, "value");
									client->valid_coils_num = json_object_array_length(value);
									for(l = 0;l < client->valid_coils_num; l++) {
										valids = json_object_array_get_idx(value, l);
										client->valid_coils[l] = atoi(json_object_get_string(valids));
									}
								} else if(strcmp_ss(json_object_get_string(val), "valid discrete inputs") == 0) {
									refs = json_object_object_get(prop, "refs");
									client->inputs_refs = json_object_get_string(refs);
									value = json_object_object_get(prop, "value");
									client->valid_inputs_num = json_object_array_length(value);
									for(l = 0; l < client->valid_inputs_num; l++) {
										valids = json_object_array_get_idx(value, l);
										client->valid_inputs[l] = atoi(json_object_get_string(valids));
									}
								} else if(strcmp_ss(json_object_get_string(val), "valid holding registers") == 0) {
									refs = json_object_object_get(prop, "refs");
									client->hregs_refs = json_object_get_string(refs);
									value = json_object_object_get(prop, "value");
									client->valid_hregs_num = json_object_array_length(value);
									for(l = 0;l < client->valid_hregs_num; l++) {
										valids = json_object_array_get_idx(value, l);
										client->valid_hregs[l] = atoi(json_object_get_string(valids));
									}
								} else if(strcmp_ss(json_object_get_string(val), "valid input registers") == 0) {
									refs = json_object_object_get(prop, "refs");
									client->iregs_refs = json_object_get_string(refs);
									value = json_object_object_get(prop, "value");
									client->valid_iregs_num = json_object_array_length(value);
									for(l = 0; l < client->valid_iregs_num; l++) {
										valids = json_object_array_get_idx(value, l);
										client->valid_iregs[l] = atoi(json_object_get_string(valids));
									}
								}

								if(client->baudrate > 0 && client->address) {
									modbus_t *ctx = modbus_new_rtu(client->address, client->baudrate, 'N', 8, 1);
									if (ctx == NULL) {
								   		fprintf(stderr, "Unable to allocate libmodbus context\n");
								   		continue;
									}
									modbus_set_slave(ctx, client->server_id);
									modbus_set_debug(ctx, TRUE);
									modbus_set_error_recovery(ctx,
									                              MODBUS_ERROR_RECOVERY_LINK |
									                              MODBUS_ERROR_RECOVERY_PROTOCOL);
									if (modbus_connect(ctx) == -1) {
										fprintf(stderr, "Connection failed: %s\n", modbus_strerror(errno));
										modbus_free(ctx);
										continue;
									}
									client->ctx = ctx;
									client->predefined = TRUE;
								}
							}
						}
					}
				}
			}
		}
	}
	thread_loop();
	free(mbclients);
	mbclients = NULL;
}

static void plugin_stop(void)
{
	stopflag = 1;
}

int main(int argc, char** argv)
{
	char *cli_cfgfile = NULL;
	cfg_data_t *cli_cfgdata = NULL;
	if(argc < 2) {
		printf("usage: plugin_main <plugin folder>\n");
		return -1;
	}
	cli_cfgfile = argv[1];
	signal(SIGPIPE, SIG_IGN);

	cli_cfgdata = cfg_loads(cli_cfgfile);
	cli_setcallback(plugin_call);

	cli_start(cli_cfgdata);
	plugin_start();
	
	return 0;
}

