import json
import os
import sys
import urllib.error
import urllib.request


def load_release_bytes(env_name, path):
    url = os.environ.get(env_name)
    if url:
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.read(), url
        except urllib.error.URLError as error:
            print(f"{env_name} 에서 파일을 받지 못해 건너뜁니다: {error}", file=sys.stderr)
            return None, None

    if path.exists():
        return path.read_bytes(), path

    return None, None


def load_release_data(env_name, path):
    data, source = load_release_bytes(env_name, path)
    if data is None:
        return None, None

    try:
        return json.loads(data.decode("utf-8")), source
    except ValueError as error:
        print(f"{source} 형식이 올바르지 않아 건너뜁니다: {error}", file=sys.stderr)
        return None, None
