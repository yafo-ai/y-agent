import requests
import json

xbot_server = 'http://193.111.99.44:5887/'

xbot_client_user_id="1688857198674249"

def send_text_msg(client_id,conversation_id,content):
    try:
        data = {
            "type": "WW_SEND_TEXT_MSG",
            "client_id": client_id,
            "data": {
                "content": content,
                "conversation_id": conversation_id
            }
        }
        json_data = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        response = requests.post(xbot_server, data=json_data, headers=headers)
    except Exception as e:
        print(f"Xbot Error: {e}")