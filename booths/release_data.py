import json
import os
import sys
import urllib.error
import urllib.request


def load_release_data(env_name, path):
    url = os.environ.get(env_name)
    if url:
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.loads(response.read().decode("utf-8")), url
        except (urllib.error.URLError, ValueError) as error:
            print(f"{env_name} 에서 파일을 받지 못해 건너뜁니다: {error}", file=sys.stderr)
            return None, None

    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")), path

    return None, None
