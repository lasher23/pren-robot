import requests

base_url = "http://prenh22-nschmi01.el.eee.intern"


def post_move(alpha, beta, gamma):
    payload = {
        "alpha": {"fromAngle": alpha[0], "toAngle": alpha[1], "duration": alpha[2]},
        "beta": {"fromAngle": beta[0], "toAngle": beta[1], "duration": beta[2]},
        "gamma": {"fromAngle": gamma[0], "toAngle": gamma[1], "duration": gamma[2]}
    }
    post = requests.post("%s/api/positions" % base_url, json=payload)


def post_object(type):
    payload = {
        "type": type
    }
    post = requests.post("%s/api/objects" % base_url, json=payload)


def start_run():
    requests.post("%s/api/startrun" % base_url)


def stop_run():
    requests.post("%s/api/stoprun" % base_url)
