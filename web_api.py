import requests


def post_move(alpha, beta, gamma):
    payload = {
        "alpha": {"fromAngle": alpha[0], "toAngle": alpha[1], "duration": alpha[2]},
        "beta": {"fromAngle": beta[0], "toAngle": beta[1], "duration": beta[2]},
        "gamma": {"fromAngle": gamma[0], "toAngle": gamma[1], "duration": gamma[2]}
    }
    post = requests.post("http://localhost:3333/api/positions", json=payload)
