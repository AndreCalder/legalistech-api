import os
import requests


# controllers/util/enlace_base.py
import os, requests, json

class EnlaceBase:
    enlace_key = os.getenv("ENLACE_KEY")

    def make_request(self, endpoint, method="GET", data=None, headers=None, override=None):
        """
        method: the logical HTTP method (GET/POST/PATCH/DELETE)
        override: if set, sends POST on the wire with X-Http-Method-Override=<override>
        headers: extra headers to merge
        """
        url = f"https://api.fiducia.com.mx/enlace/v1/{endpoint}?apikey={self.enlace_key}"

        # Base headers
        final_headers = {"Content-Type": "application/json"}
        if headers:
            final_headers.update(headers)

        # Enlace often uses POST + X-Http-Method-Override
        actual_method = "POST" if override else method
        if override:
            final_headers["X-Http-Method-Override"] = override
        else:
            # keep compatibility with your old usage that set override=method
            final_headers.setdefault("X-Http-Method-Override", method)

        try:
            resp = requests.request(actual_method, url, headers=final_headers, data=data, timeout=15)
            if resp.status_code != 200:
                return {"error": f"status {resp.status_code}", "body": resp.text}
            try:
                return resp.json()
            except ValueError:
                return {"error": "invalid_json", "body": resp.text}
        except requests.RequestException as e:
            return {"error": "network", "body": str(e)}

