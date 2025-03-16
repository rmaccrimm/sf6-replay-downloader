import json
import os
from datetime import datetime
from pathlib import Path

import defopt
import requests


def main(conf_file: str):
    with open(conf_file) as f:
        args = json.loads(f.read())

        PLAYER_SID = args["PLAYER_SID"]
        COOKIE = args["COOKIE"]

    curr_file = Path(__file__)
    data_dir = Path(os.path.join(str(curr_file.parent), "data", "json"))
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
        "Referer": f"https://www.streetfighter.com/6/buckler/profile/{PLAYER_SID}",
        "Cookie": COOKIE,
        "Priority": "u=3, i",
        "x-nextjs-data": "1",
    }

    replays = []
    for page in range(1, 11):
        url = (
            "https://www.streetfighter.com/6/buckler/_next/data/yDWIiI2UnQLmZkd4ZwzOV/en/profile/"
            f"{PLAYER_SID}/battlelog.json?page={page}&sid={PLAYER_SID}"
        )
        r = requests.get(url, headers=headers).json()
        for d in r["pageProps"]["replay_list"]:
            replays.append(d)

    dt = datetime.now()
    fname = os.path.join(str(data_dir), f"replays_{int(dt.timestamp())}.json")
    with open(fname, "w+") as f:
        f.write(json.dumps({"replay_list": replays}))

    print(fname)


if __name__ == "__main__":
    defopt.run(main)
