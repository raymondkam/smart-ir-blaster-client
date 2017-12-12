import subprocess
import thread
import time
import json

with open('./config/websocket.json') as json_data:
    websocketJSON = json.load(json_data)
    health_check_server_address = websocketJSON["health_check_server_address"]

health_check_interval = 60

def formatted_time():
    return time.strftime('%l:%M%p %Z on %b %d, %Y')

def keep_websocket_server_alive():
    while True:
        print("\n{} ### Checking websocket server health ###").format(formatted_time())
        subprocess.call(["curl", "-X", "GET", health_check_server_address])
        time.sleep(health_check_interval)

if __name__ == "__main__":
    keep_websocket_server_alive()

