import sys
import time
import re
from hashlib import sha256
import requests

PROTOCOL = "http"
HOST = "speedport.ip"
CSRF_TOKEN = "nulltoken"
PARAMS = {"lang": "de"}


def create_absolute_url(endpoint):
    return PROTOCOL + "://" + HOST + endpoint


def change_connection_status(connectionStatus):
    ensure_session()
    response = SESSION.post(
        create_absolute_url("/data/Connect.json"),
        params=PARAMS,
        data={
            'req_connect': connectionStatus,
            'csrf_token': CSRF_TOKEN
        })
    return response.status_code == 200


def ensure_session():
    if is_logged_in():
        update_csrf()
        return
    response = SESSION.get(create_absolute_url("/data/challenge.json"))
    challenge = get_token("challenge", response.text)
    password = (sha256(
        str(challenge + ":" + str(DEVICE_PASSWORD)).encode('utf-8'))
        .hexdigest())
    data = {
        'csrf_token': CSRF_TOKEN,
        'showpw': '0',
        'challengev': challenge,
        'password': password
    }
    response = SESSION.post(
        create_absolute_url("/data/Login.json"), params=PARAMS, data=data)
    SESSION.cookies.set("challengev", challenge, domain='speedport.ip')
    return is_logged_in()


def extract_variable(json, key):
    return re.match("\"varid\"\\s*:\\s*\"" + key +
                    "\",\\s*\"varvalue\"\\s*:\\s*\"([^\"]+)", json)


def get_external_ip():
    raise NotImplementedError


def get_token(token, content):
    match = re.findall('var ' + token + ' = "(.*?)";', content)
    if len(match) == 1:
        return match[0]


def is_logged_in():
    return SESSION.cookies.get("SessionID_R3") is not None


def logout():
    raise NotImplementedError


def update_csrf():
    if is_logged_in():
        response = SESSION.get(
            create_absolute_url(
                "/html/content/internet/connection.html?lang=de"))
        global CSRF_TOKEN
        CSRF_TOKEN = get_token("csrf_token", response.text)


if len(sys.argv) != 2:
    raise SyntaxError('Syntax is: python recconect.py <device password>')

DEVICE_PASSWORD = sys.argv[1]
SESSION = requests.Session()
if ensure_session():
    if change_connection_status('disabled'):
        time.sleep(5)
        change_connection_status('online')
        print('Done!')
