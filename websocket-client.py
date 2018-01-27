import subprocess
import websocket
import thread
import threading
import time
import json
import ssl

with open('./config/websocket.json') as json_data:
    websocket_json = json.load(json_data)
    token = websocket_json["token"]
    server_address = websocket_json["server_address"]

with open('./config/commands.json') as commands_data:
    commands_json = json.load(commands_data)

with open('./config/ps4_commands.json') as ps4_commands_data:
    ps4_commands_json = json.load(ps4_commands_data)

ping_interval = 30
reconnect_interval = 10
samsung_remote_ir_ids = ["KEY_MUTE", "KEY_VOLUMEUP", "KEY_VOLUMEDOWN"]
samsung_discrete_ir_ids = ["POWER_ON", "POWER_OFF", "SOURCE_TV", "SOURCE_HDMI1","SOURCE_HDMI2"]

def formatted_time():
    return time.strftime('%l:%M%p %Z on %b %d, %Y')

def ir_send(remote_name, ir_id, delay, num_times):
    time.sleep(delay)
    print("\n{} IR: Sending IR command {} on {}").format(formatted_time(), ir_id, remote_name)
    error = subprocess.call(["irsend", "-#", str(num_times), "SEND_ONCE", remote_name, ir_id])
    if error:
        print("{} IR: sending IR command {} {} times on {} failed").format(formatted_time(), ir_id, num_times, remote_name)
    else:
        print("{} IR: sending IR command {} {} times on {} succeeded").format(formatted_time(), ir_id, num_times, remote_name)

def ps4_waker_send(ps4_waker_subprocess_params):
    print("\n{} PS4: Sending PS4 waker command with {}").format(formatted_time(), ps4_waker_subprocess_params)

    error = subprocess.call(ps4_waker_subprocess_params)
    if error:
        print("{} PS4: sending PS4 command {} failed").format(formatted_time, ps4_waker_subprocess_params)
    else:
        print("{} PS4: sending PS4 command {}  succeeded").format(formatted_time(), ps4_waker_subprocess_params)

def handle_command_ps4(ps4_commands_json, command_id):
    subprocess_params = ps4_commands_json[command_id]
    ps4_waker_send(subprocess_params)
    return

def on_message(ws, message):
    message_json = json.loads(message)
    if message_json["type"] == "auth":
        if message_json["message"] == "success":
            print("{} WS: auth success").format(formatted_time())
        else:
            print("{} WS: auth failed").format(formatted_time())
    elif message_json["type"] == "command":
        print("\n{} IR: Received command:").format(formatted_time())
        command_id = message_json["message"]

        # handle ps4 command in new thread
        if command_id in ps4_commands_json: 
            ps4_thread = threading.Thread(target=handle_command_ps4, args=(ps4_commands_json, command_id,))
            ps4_thread.start()

        # handle tv commands
        command_json = commands_json[command_id]
        name = command_json["name"]
        commands = command_json["commands"]
        print("{} IR: command name: {}").format(formatted_time(), name)
        print("{} IR: commands: {}").format(formatted_time(), commands)
        for command in commands:
            ir_id = command["id"]
            delay = float(command["delay"])
            num_times = int(command.get("numTimes", "1"))
            if ir_id in samsung_remote_ir_ids:
                ir_send("SAMSUNG_REMOTE", ir_id, delay, num_times)
            elif ir_id in samsung_discrete_ir_ids:
                ir_send("SAMSUNG_DISCRETE", ir_id, delay, num_times)
            else:
                print("{} Unrecognized IR id").format(formatted_time())

    elif message_json["type"] == "pong":
        print("{} WS: received pong").format(formatted_time())
def on_error(ws, error):
    print(error)

def on_close(ws):
    print("{} ### closed ###").format(formatted_time())
    time.sleep(reconnect_interval)
    connect_to_websocket_server()

def on_open(ws):
    def ping(*args):
        while True:
            time.sleep(ping_interval)
            print("{} WS: sending ping").format(formatted_time())
            ws.send(json.dumps({"token": token, "type": "ping"}))
    thread.start_new_thread(ping, ())

    print("{} ### websocket opened ###").format(formatted_time())
    ws.send(json.dumps({"token": token, "type": "auth"}))

def connect_to_websocket_server():
    print("{} ### connecting to websocket server ###").format(formatted_time())
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://" + server_address,
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

if __name__ == "__main__":
    connect_to_websocket_server()
