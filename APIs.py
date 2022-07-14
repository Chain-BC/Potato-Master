import requests
import json


# Meme api
def get_meme():
    response = requests.get("https://meme-api.herokuapp.com/gimme")
    json_data = json.loads(response.text)
    meme = json_data['url']
    return meme
