import requests
import json


# Meme api
def get_meme():
    response = requests.get("https://meme-api.herokuapp.com/gimme")
    json_data = json.loads(response.text)
    meme = json_data['url']
    return meme


def get_wholesomememe():
    response = requests.get("https://meme-api.herokuapp.com/gimme/wholesomememes")
    json_data = json.loads(response.text)
    meme = json_data['url']
    return meme


def get_dankmeme():
    response = requests.get("https://meme-api.herokuapp.com/gimme/dankmemes")
    json_data = json.loads(response.text)
    meme = json_data['url']
    return meme


def get_meirlmeme():
    response = requests.get("https://meme-api.herokuapp.com/gimme/me_irl")
    json_data = json.loads(response.text)
    meme = json_data['url']
    return meme
