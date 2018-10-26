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

""" Send File Using MQTT """
import time
import paho.mqtt.client as paho
import hashlib
broker = "127.0.0.1"
filename = "blob.png"
topic = "proj_1/gw_1/blob0"
qos = 1
data_block_size = 2000
fo = open(filename, "rb")

def on_publish(client, userdata, mid):
    #logging.debug("pub ack "+ str(mid))
    client.mid_value = mid
    client.puback_flag = True

# waitfor loop


def wait_for(client, msgType, period=0.25, wait_time=40, running_loop=False):
    client.running_loop = running_loop  # if using external loop
    wcount = 0
    while True:
        #print("waiting"+ msgType)
        if msgType == "PUBACK":
            if client.on_publish:
                if client.puback_flag:
                    return True

        if not client.running_loop:
            client.loop(.01)  # check for messages manually
        time.sleep(period)
        #print("loop flag ",client.running_loop)
        wcount += 1
        if wcount > wait_time:
            print("return from wait loop taken too long")
            return False
    return True


def send_header(filename):
    header = "START" + ":" + filename + ":"
    header = bytearray(header, "utf-8")
    header.extend(b'-' * (0xFF - len(header)))
    print(header)
    c_publish(client, topic, header, qos)


def send_end(filename):
    end = "END" + ":" + out_hash_md5.hexdigest() + ":"
    end = bytearray(end, "utf-8")
    end.extend(b'-' * (0xFF - len(end)))
    print(end)
    c_publish(client, topic, end, qos)


def c_publish(client, topic, out_message, qos):
    res, mid = client.publish(topic, out_message, qos)  # publish
    if res == 0:  # published ok
        if wait_for(client, "PUBACK", running_loop=True):
            if mid == client.mid_value:
                print("match mid ", str(mid))
                client.puback_flag = False  # reset flag
            else:
                raise SystemExit("not got correct puback mid so quitting")

        else:
            raise SystemExit("not got puback so quitting")


# create client object client1.on_publish = on_publish
# #assign function to callback client1.connect(broker,port)
# #establish connection client1.publish("data/files","on")
client = paho.Client("client-001")
######
# client.on_message=on_message
client.on_publish = on_publish
client.puback_flag = False  # use flag in publish ack
client.mid_value = None
#####
print("connecting to broker ", broker)
client.connect(broker)  # connect
client.loop_start()  # start loop to process received messages
# print("subscribing ")
# client.subscribe(topic)#subscribe
time.sleep(2)
start = time.time()
print("publishing ")
send_header(filename)
Run_flag = True
count = 0
out_hash_md5 = hashlib.md5()
# in_hash_md5 = hashlib.md5()

while Run_flag:
    chunk = fo.read(data_block_size)
    if chunk:
        out_hash_md5.update(chunk)  # update hash
        out_message = chunk
        #print(" length =",type(out_message))
        c_publish(client, topic, out_message, qos)

    else:
        # end of file so send hash
        out_message = out_hash_md5.hexdigest()
        send_end(filename)
        #print("out Message ",out_message)
        # res,mid=client.publish(topic,out_message,qos=1)#publish
        Run_flag = False
time_taken = time.time() - start
print("took ", time_taken)
time.sleep(4)
client.disconnect()  # disconnect
client.loop_stop()  # stop loop
fo.close()
