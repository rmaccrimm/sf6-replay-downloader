import json
import os
import re
from datetime import datetime
from pathlib import Path

import defopt
import requests


def get_build_id() -> str:
    r = requests.get(
        "https://www.streetfighter.com/6/buckler",
        headers={
            "Sec-Fetch-Dest": "empty",
            "Accept": "*/*",
            "Sec-Fetch-Site": "same-origin",
            "Accept-Language": "en-CA,en-US;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Mode": "cors",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, "
                "like Gecko) Version/18.3 Safari/605.1.15"
            ),
        },
    )
    r.raise_for_status()
    m = re.search(r'"buildId":\s*"(\w+)"', r.content.decode("utf-8"))
    if m is None:
        raise RuntimeError("Could not find buildId in page")

    return m.group(1)


def main(conf_file: str):
    with open(conf_file) as f:
        args = json.loads(f.read())

        player_sid = args["PLAYER_SID"]
        cookie = args["COOKIE"]
        data_dir = args["DATA_DIR"]

    data_dir = Path(os.path.join(data_dir, "json"))
    data_dir.mkdir(parents=True, exist_ok=True)

    headers = {
        "Sec-Fetch-Dest": "empty",
        "Accept": "*/*",
        "Sec-Fetch-Site": "same-origin",
        "Accept-Language": "en-CA,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Fetch-Mode": "cors",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, "
            "like Gecko) Version/18.3 Safari/605.1.15"
        ),
        "Referer": f"https://www.streetfighter.com/6/buckler/profile/{player_sid}",
        "Cookie": cookie,
        "Priority": "u=3, i",
        "x-nextjs-data": "1",
    }

    replays = []
    build_id = get_build_id()

    for page in range(1, 11):
        url = (
            f"https://www.streetfighter.com/6/buckler/_next/data/{build_id}/en/profile/"
            f"{player_sid}/battlelog.json?page={page}&sid={player_sid}"
        )
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        for d in r.json()["pageProps"]["replay_list"]:
            replays.append(d)

    dt = datetime.now()
    fname = os.path.join(str(data_dir), f"replays_{int(dt.timestamp())}.json")
    with open(fname, "w+") as f:
        f.write(json.dumps(replays))

    print(fname)


if __name__ == "__main__":
    defopt.run(main)
