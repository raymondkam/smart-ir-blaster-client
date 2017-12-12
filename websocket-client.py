import subprocess
import websocket
import thread
import time
import json
import ssl

with open('./config/websocket.json') as json_data:
    websocketJSON = json.load(json_data)
    token = websocketJSON["token"]
    server_address = websocketJSON["server_address"]

ping_interval = 30
reconnect_interval = 10
samsung_remote_ir_ids = ["KEY_MUTE", "KEY_VOLUMEUP", "KEY_VOLUMEDOWN"]
samsung_discrete_ir_ids = ["POWER_ON", "POWER_OFF", "SOURCE_TV", "SOURCE_HDMI1","SOURCE_HDMI2"]

def ir_send(remote_name, ir_id, delay, num_times):
    time.sleep(delay)
    print("\nIR: Sending IR command {} on {}").format(ir_id, remote_name)
    error = subprocess.call(["irsend", "-#", str(num_times), "SEND_ONCE", remote_name, ir_id])
    if error:
        print("IR: sending IR command {} {} times on {} failed").format(ir_id, num_times, remote_name)
    else:
        print("IR: sending IR command {} {} times on {} succeeded").format(ir_id, num_times, remote_name)

def on_message(ws, message):
    message_json = json.loads(message)
    if message_json["type"] == "auth":
        if message_json["message"] == "success":
            print("WS: auth success")
        else:
            print("WS: auth failed")
    elif message_json["type"] == "command":
        print("\nIR: Received command:")
        message = message_json["message"]
        name = message["name"]
        commands = message["commands"]
        print("IR: command name: {}").format(name)
        print("IR: commands: {}").format(commands)

        for command in commands:
            ir_id = command["id"]
            delay = float(command["delay"])
            num_times = int(command.get("numTimes", "1"))
            if ir_id in samsung_remote_ir_ids:
                ir_send("SAMSUNG_REMOTE", ir_id, delay, num_times)
            elif ir_id in samsung_discrete_ir_ids:
                ir_send("SAMSUNG_DISCRETE", ir_id, delay, num_times)
            else:
                print("Unrecognized IR id")
    elif message_json["type"] == "pong":
        print("WS: received pong")
def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")
    time.sleep(reconnect_interval)
    connect_to_websocket_server()

def on_open(ws):
    def ping(*args):
        while True:
            time.sleep(ping_interval)
            print("WS: sending ping")
            ws.send(json.dumps({"token": token, "type": "ping"}))
    thread.start_new_thread(ping, ())

    print("### websocket opened ###")
    ws.send(json.dumps({"token": token, "type": "auth"}))

def connect_to_websocket_server():
    print("### connecting to websocket server ###")
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://" + server_address,
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

if __name__ == "__main__":
    connect_to_websocket_server()
