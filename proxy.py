class ConsoleColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

import base64
import json
from flask import Flask, send_from_directory, abort, Response
import requests
from cachetools import TTLCache

skincache = TTLCache(maxsize=100, ttl=12 * 60 * 60)
cloakcache = TTLCache(maxsize=100, ttl=12 * 60 * 60)

app = Flask(__name__)

@app.route('/MinecraftSkins/<username>.png')
def handle_skin(username):
    if username in skincache:
        print(ConsoleColors.OKBLUE + '[SKIN] Retrieving cached skin for ' + username)
        cached_content = skincache[username]
    else:
        print(ConsoleColors.OKGREEN + '[SKIN] Fetching skin for ' + username)
        external_url = f'https://mc-heads.net/skin/{username}'
        response = requests.get(external_url)
        
        skincache[username] = response.content
        cached_content = response.content

    return Response(cached_content, content_type='image/png')

def fetch_cloak_info(username):
    uuid_url = f'https://api.mojang.com/users/profiles/minecraft/{username}'
    uuid_response = requests.get(uuid_url)

    if uuid_response.status_code != 200:
        return None
    
    user_uuid = uuid_response.json().get('id')
    
    profile_url = f'https://sessionserver.mojang.com/session/minecraft/profile/{user_uuid}'
    profile_response = requests.get(profile_url)
    
    if profile_response.status_code != 200:
        return None
    
    profile_data = profile_response.json()
    textures_value = profile_data.get('properties', [{}])[0].get('value', '')
    
    try:
        decoded_textures = json.loads(base64.b64decode(textures_value).decode('utf-8'))
        cloak_url = decoded_textures.get('textures', {}).get('CAPE', {}).get('url')
        return cloak_url
    except Exception as e:
        print("Error decoding textures:", e)
        return None

@app.route('/MinecraftCloaks/<username>.png')
def handle_cloak(username):
    if username in cloakcache:
        print(ConsoleColors.OKBLUE + '[CLOAK] Retrieving cached cloak for ' + username)
        cloak_url = cloakcache[username]
    else:
        print(ConsoleColors.OKGREEN + '[CLOAK] Fetching cloak for ' + username)
        cloak_url = fetch_cloak_info(username)
        cloakcache[username] = cloak_url
    
    if cloak_url:
        cloak_content = requests.get(cloak_url).content
        return Response(cloak_content, content_type='image/png')
    else:
        abort(404)

if __name__ == '__main__':
    app.run(port=5959, host="0.0.0.0")