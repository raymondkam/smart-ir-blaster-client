import websocket
import thread
import time
import json
import ssl

with open('./config/websocket.json') as json_data:
    token = json.load(json_data)["token"]

def on_message(ws, message):
    message_json = json.loads(message)
    if message_json["type"] == "auth":
        if message_json["message"] == "success":
            print("websocket auth success")
        else:
            print("websocket auth failed")
    elif message_json["type"] == "command":
        print("\nReceived command:")
        message = message_json["message"]
        name = message["name"]
        commands = message["commands"]
        print("name: {}").format(name)
        print("commands: {}").format(commands)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    print("### websocket opened ###")
    ws.send(json.dumps({"token": token, "type": "auth"}))

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://localhost:8080",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
