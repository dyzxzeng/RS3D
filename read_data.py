import socket as s
import subprocess
import threading
import queue
import time
import struct
import paho.mqtt.client as mqtt
import re
import os
from paho.mqtt.client import CallbackAPIVersion
import uuid
import sys
import netifaces



# Initialize a queue for multi-threading
data_queue = queue.Queue(2000)
def mac_address():

   macEth = None
   data = netifaces.interfaces()
   for i in data:
      if i == 'wlan0': #'en0': # 'eth0':
         interface = netifaces.ifaddresses(i)
         info = interface[netifaces.AF_LINK]
         if info:
            macEth = interface[netifaces.AF_LINK][0]["addr"]

   return macEth

# def get_mac_address(interface="eth0"):
#     try:
#         # Run ifconfig (works on older systems)
#         result = subprocess.run(["ifconfig", interface], capture_output=True, text=True)
#         output = result.stdout

#         # Fallback to "ip link show" for newer systems if ifconfig fails
#         if not output:
#             result = subprocess.run(["ip", "link", "show", interface], capture_output=True, text=True)
#             output = result.stdout

#         # Regex to extract MAC address (matches standard MAC format XX:XX:XX:XX:XX:XX)
#         mac_match = re.search(r"([0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2})", output)

#         if mac_match:
#             return mac_match.group(1)  # Extracted MAC address
#         else:
#             return None  # MAC address not found

#     except Exception as e:
#         print(f"Error retrieving MAC address: {e}")
#         return None

# Read the device information from system
with open('/opt/settings/sys/ip.txt', 'r') as file:
    host = file.read().strip()

if struct.calcsize("L") == 4:
    timestamp_byte = "Q"
elif struct.calcsize("L") == 8:
    timestamp_byte = "L"

# unit = get_mac_address("eth0")
unit = mac_address()
print(f'unit={unit}')
# Port information for sensor
port = 8888                             # Port to bind to
sock = s.socket(s.AF_INET, s.SOCK_DGRAM | s.SO_REUSEADDR)
print("Waiting for data on Port:", port, "Mac address:", host)
# host = "192.168.12.111"
sock.bind((host, port))

sampling_rate = 100
sensitivity = float('3.60E+08')
cnt = 0

# MQTT Configuration
MQTT_BROKER = "My MQTT Broker"
MQTT_PORT = 0
MQTT_user = None
MQTT_password = None
MQTT_TOPIC_PRE = f"/UGA/{unit.replace(':', '')}/"
DATA_INTERVAL = 10000  # 100Hz (10,000 microseconds between samples)

# Function to receive data (Producer)
def receive_data():
    while True:
        data, addr = sock.recvfrom(1024)  # Wait for data
        data_queue.put(data)  # Add received data to queue

def pack_beddot_data(mac_addr, timestamp, data_interval, data):
   # First, convert the MAC address into byte sequence
   mac_bytes = bytes.fromhex(mac_addr.replace(':', ''))

   # Then, pack each data item sequentially
   packed_data = struct.pack("!BBBBBB", *mac_bytes)
   packed_data += struct.pack("H", len(data))  # data length
   packed_data += struct.pack(timestamp_byte, timestamp)  # timestamp
   packed_data += struct.pack("I", data_interval)  # data interval 

   # pack measurement data
   for item in data:
       packed_data += struct.pack("i", item)

   return packed_data


# Function to Publish data
def upload_data(client):
    """Retrieves data from the queue and uploads it via MQTT."""
    # Try connecting to the broker
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 30)
        client.loop_start()
    except Exception as e:
        print(f"Error connecting to MQTT: {e}")
        sys.exit(1)

    while True:
        if not data_queue.empty():
            data = data_queue.get()
            data = data.rstrip(b'}').split(b',')
            channel = data.pop(0).decode('utf-8')[-2]
            start_timestamp = int(float(data.pop(0)) * 1000000)
            int_data_list = [int(data_point.decode('utf-8').strip()) for data_point in data]
            # Pack and send the sine wave data series
            packed_data = pack_beddot_data(unit, start_timestamp, DATA_INTERVAL, int_data_list)
            if channel == 'Z':
                channel = 'geophone'
            elif channel == 'E':
                channel = 'X'
            elif channel == 'N':
                channel = 'Y'
            MQTT_TOPIC = MQTT_TOPIC_PRE + channel
            # print(packed_data, MQTT_TOPIC)
            client.publish(MQTT_TOPIC, packed_data, qos=1)




def is_all_threads_alive(thd_list):
    alive=True
    for t in thd_list:
        if not t.is_alive():
            alive=False
            break
    return alive


if __name__ == '__main__':
    thread_list = []

    # Receiver
    receiver_thread = threading.Thread(target=receive_data, daemon=True)
    receiver_thread.start()
    thread_list.append(receiver_thread)

    # MQTT
    unique_client_id = f"client_{uuid.uuid4()}"
    mqtt_client = mqtt.Client(client_id=unique_client_id, callback_api_version=CallbackAPIVersion.VERSION2)
    if MQTT_user is not None:
        mqtt_client.username_pw_set(username=MQTT_user, password=MQTT_password)


    mqtt_thread = threading.Thread(target=upload_data, args=(mqtt_client,), daemon=True)
    mqtt_thread.start()
    thread_list.append(mqtt_thread)
    cnt = 0
    while True:
        time.sleep(1)
        cnt += 1
        # print(cnt, data_queue.qsize())
        if not is_all_threads_alive(thread_list):
            break

    mqtt_client.disconnect()
    time.sleep(2)
    sys.exit()
