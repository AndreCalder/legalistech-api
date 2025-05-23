import os
import json
import requests

class EnlaceBase:
    enlace_url = "https://api.fiducia.com.mx/enlace/v1/"
    enlace_key = os.getenv("ENLACE_KEY")

    # Generic requester for Enlace API
    def make_request(self, endpoint, method="GET", request_params=None, data=None):
        url = self.enlace_url + endpoint
        params = {"apikey": self.enlace_key}
        if request_params:
            params = {**params, **request_params}

        headers = {"Content-Type": "application/json"}
        if method == "POST":
            headers["X-Http-Method-Override"] = "GET"
        print(data)
        return requests.request(
            method,
            url,
            headers=headers,
            params=params,
            data=data,
            timeout=15
        ).json()
