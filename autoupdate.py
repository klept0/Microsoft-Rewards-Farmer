import os
import sys
from io import BytesIO
from zipfile import ZipFile

import requests


def update(version: str):
    url = "https://github.com/klept0/MS-Rewards-Farmer/archive/refs/heads/master.zip"
    folderName = "MS-Rewards-Farmer-master"
    with open(".gitignore", "r") as f:
        exclusions = f.read().splitlines()
        exclusions = [e for e in exclusions if e != "" and not e.startswith("#")] + [
            ".gitignore",
            ".git",
            "autoupdate.py",
        ]
    print("Removing old files...")
    for root, dirs, files in os.walk(".", topdown=False):
        for name in files:
            path = os.path.join(root, name)
            relativePath = path[2:]
            if not relativePath.startswith(tuple(exclusions)):
                os.remove(path)
    print("Downloading...")
    r = requests.get(url)
    print(f"Download status code: {r.status_code}")
    data = BytesIO(r.content)
    print("Extracting...")
    with ZipFile(data, "r") as zipObj:
        files = [
            f
            for f in zipObj.namelist()
            if f.startswith(folderName) and not f.endswith("/")
        ]
        for file in files:
            newName = file.replace(f"{folderName}/", "")
            if not os.path.exists(newName):
                newPath = os.path.join(".", newName)
                os.makedirs(os.path.dirname(newPath), exist_ok=True)
                with zipObj.open(file) as src, open(newPath, "wb") as dst:
                    dst.write(src.read())
                    print(f"Copied {newName}!")
    with open("version.txt", "w") as f:
        f.write(version)
    print("Done !")


def getCurrentVersion():
    if os.path.exists("version.txt"):
        with open("version.txt", "r") as f:
            version = f.read()
        return version
    return None


def getLatestVersion():
    r = requests.get(
        "https://api.github.com/repos/klept0/MS-Rewards-Farmer/commits/master"
    )
    return r.json()["sha"]


if __name__ == "__main__":
    currentVersion = getCurrentVersion()
    latestVersion = getLatestVersion()
    if currentVersion != latestVersion:
        print("New version available !")
        update(latestVersion)

    print("Starting...")

    import main

    main.sys.argv[1:] = sys.argv[1:]
    main.main()
