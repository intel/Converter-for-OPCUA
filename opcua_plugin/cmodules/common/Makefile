# Copyright (c) 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

CC=gcc
CFLAGS= -I./json-c/ -I./rabbitmq-c/librabbitmq -I./safestringlib-c/include
# LDFLAGS= json-c/.libs/libjson-c.a rabbitmq-c/build/librabbitmq/librabbitmq.a -lpthread

LIBJSON := \
	json-c

RABBITMQ-C := \
	rabbitma-c

SAFESTRING := \
	safestringlib-c

LIB_TARGET = libplugin-c.a

SOURCE = $(wildcard *.c)
OBJS = $(patsubst %.c,%.o,$(SOURCE))

%.o: %.c
	$(CC) -c -o $@ $< $(CFLAGS)

all: $(LIBJSON) $(RABBITMQ-C) $(SAFESTRING) $(LIB_TARGET)

$(LIB_TARGET): $(OBJS)
	$(AR) cq $@ $^

clean:
	rm -f $(LIB_TARGET)
	rm -f $(OBJS)
	rm -r rabbitmq-c/build;\
	cd json-c;\
	cd safestringlib-c;\
	make clean

json-c-0.13-20171207.tar.gz:
	if [ ! -f "json-c-0.13-20171207.tar.gz" ]; then \
		wget -c https://github.com/json-c/json-c/archive/json-c-0.13-20171207.tar.gz; \
	fi;

$(LIBJSON): json-c-0.13-20171207.tar.gz
	if [ ! -d "json-c" ]; then \
		tar zxvf json-c-0.13-20171207.tar.gz; \
		mv json-c-json-c-0.13-20171207 json-c; \
	fi; \
	cd json-c; \
	sh autogen.sh; \
	./configure; \
	make

rabbitmq-c-v0.8.0.tar.gz:
	if [ ! -f "v0.8.0.tar.gz" ]; then \
		wget -c https://github.com/alanxz/rabbitmq-c/archive/v0.8.0.tar.gz; \
	fi;

$(RABBITMQ-C): rabbitmq-c-v0.8.0.tar.gz
	if [ ! -d "rabbitmq-c" ]; then \
		tar zxvf v0.8.0.tar.gz; \
		mv rabbitmq-c-0.8.0 rabbitmq-c; \
	fi
	mkdir -p rabbitmq-c/build; \
	cd rabbitmq-c/build; \
	cmake ..; \
	cmake --build .

safestringlib-c-77b772849eda2321fb0dca56a321e3939930d7b9:
	if [ ! -f "77b772849eda2321fb0dca56a321e3939930d7b9" ]; then \
		wget -c https://codeload.github.com/intel/safestringlib/zip/77b772849eda2321fb0dca56a321e3939930d7b9; \
	fi;

$(SAFESTRING): safestringlib-c-77b772849eda2321fb0dca56a321e3939930d7b9
	if [ ! -d "safestringlib-c" ]; then \
		unzip 77b772849eda2321fb0dca56a321e3939930d7b9; \
		mv safestringlib-77b772849eda2321fb0dca56a321e3939930d7b9 safestringlib-c; \
	fi; \
	cd safestringlib-c; \
	make

.PHONY: all clean $(LIBJSON) $(RABBITMQ-C) $(SAFESTRING)
