import os
import requests


class EnlaceBase:
    enlace_key = os.getenv("ENLACE_KEY")

    # Generic requester for Enlace API
    def make_request(self, endpoint, method="GET", data=None):
        url = (
            f"https://api.fiducia.com.mx/enlace/v1/{endpoint}?apikey={self.enlace_key}"
        )
        headers = {
            "Content-Type": "application/json",
            "X-Http-Method-Override": method
        }

        response = requests.request(method, url, headers=headers, data=data, timeout=15)
        return response.json()
