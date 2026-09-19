import json
import os
import urllib.request


def load_release_data(env_name, path):
    url = os.environ.get(env_name)
    if url:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode("utf-8")), url

    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")), path

    return None, None
