import argparse
import atexit
import csv
import json
import logging
import logging.handlers as handlers
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

from src import (
    Browser,
    DailySet,
    Login,
    MorePromotions,
    PunchCards,
    Searches,
)
from src.loggingColoredFormatter import ColoredFormatter
from src.utils import Utils

POINTS_COUNTER = 0


def main():
    args = argumentParser()
    setupLogging()
    loadedAccounts = setupAccounts()
    # Register the cleanup function to be called on script exit
    atexit.register(cleanupChromeProcesses)

    # Load previous day's points data
    previous_points_data = load_previous_points_data()

    for currentAccount in loadedAccounts:
        try:
            earned_points = executeBot(currentAccount, args)
            account_name = currentAccount.get("username", "")
            previous_points = previous_points_data.get(account_name, 0)

            # Calculate the difference in points from the prior day
            points_difference = earned_points - previous_points

            # Append the daily points and points difference to CSV and Excel
            log_daily_points_to_csv(account_name, earned_points, points_difference)

            # Update the previous day's points data
            previous_points_data[account_name] = earned_points

            logging.info(f"[POINTS] Data for '{account_name}' appended to the file.")
        except Exception as e:
            Utils.send_notification("⚠️ Error occurred, please check the log", str(e))
            logging.exception(f"{e.__class__.__name__}: {e}")

    # Save the current day's points data for the next day in the "logs" folder
    save_previous_points_data(previous_points_data)
    logging.info("[POINTS] Data saved for the next day.")


def log_daily_points_to_csv(date, earned_points, points_difference):
    logs_directory = Path(__file__).resolve().parent / "logs"
    csv_filename = logs_directory / "points_data.csv"

    # Create a new row with the date, daily points, and points difference
    date = datetime.now().strftime("%Y-%m-%d")
    new_row = {
        "Date": date,
        "Earned Points": earned_points,
        "Points Difference": points_difference,
    }

    fieldnames = ["Date", "Earned Points", "Points Difference"]
    is_new_file = not csv_filename.exists()

    with open(csv_filename, mode="a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if is_new_file:
            writer.writeheader()

        writer.writerow(new_row)


def setupLogging():
    format = "%(asctime)s [%(levelname)s] %(message)s"
    terminalHandler = logging.StreamHandler(sys.stdout)
    terminalHandler.setFormatter(ColoredFormatter(format))

    logs_directory = Path(__file__).resolve().parent / "logs"
    logs_directory.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format=format,
        handlers=[
            handlers.TimedRotatingFileHandler(
                logs_directory / "activity.log",
                when="midnight",
                interval=1,
                backupCount=2,
                encoding="utf-8",
            ),
            terminalHandler,
        ],
    )


def cleanupChromeProcesses():
    # Use psutil to find and terminate Chrome processes
    for process in psutil.process_iter(["pid", "name"]):
        if process.info["name"] == "chrome.exe":
            try:
                psutil.Process(process.info["pid"]).terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass


def argumentParser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MS Rewards Farmer")
    parser.add_argument(
        "-v", "--visible", action="store_true", help="Optional: Visible browser"
    )
    parser.add_argument(
        "-l", "--lang", type=str, default=None, help="Optional: Language (ex: en)"
    )
    parser.add_argument(
        "-g", "--geo", type=str, default=None, help="Optional: Geolocation (ex: US)"
    )
    parser.add_argument(
        "-p",
        "--proxy",
        type=str,
        default=None,
        help="Optional: Global Proxy (ex: http://user:pass@host:port)",
    )
    parser.add_argument(
        "-vn",
        "--verbosenotifs",
        action="store_true",
        help="Optional: Send all the logs to the notification service",
    )
    parser.add_argument(
        "-cv",
        "--chromeversion",
        type=int,
        default=None,
        help="Optional: Set fixed Chrome version (ex. 118)",
    )
    return parser.parse_args()


def setupAccounts() -> list:
    """Sets up and validates a list of accounts loaded from 'accounts.json'."""

    def validEmail(email: str) -> bool:
        """Validate Email."""
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return bool(re.match(pattern, email))

    accountPath = Path(__file__).resolve().parent / "accounts.json"
    if not accountPath.exists():
        accountPath.write_text(
            json.dumps(
                [{"username": "Your Email", "password": "Your Password"}], indent=4
            ),
            encoding="utf-8",
        )
        noAccountsNotice = """
    [ACCOUNT] Accounts credential file "accounts.json" not found.
    [ACCOUNT] A new file has been created, please edit with your credentials and save.
    """
        logging.warning(noAccountsNotice)
        exit()
    loadedAccounts = json.loads(accountPath.read_text(encoding="utf-8"))
    for account in loadedAccounts:
        if not validEmail(account["username"]):
            logging.error(f"[CREDENTIALS] Wrong Email Address: '{account['username']}'")
            exit()
    random.shuffle(loadedAccounts)
    return loadedAccounts


def executeBot(currentAccount, args: argparse.Namespace):
    logging.info(
        f"********************{currentAccount.get('username', '')}********************"
    )
    
    accountPointsCounter = 0
    remainingSearches = 0
    remainingSearchesM = 0
    startingPoints = 0

    with Browser(mobile=False, account=currentAccount, args=args) as desktopBrowser:
        utils = desktopBrowser.utils
        accountPointsCounter = Login(desktopBrowser).login()
        startingPoints = accountPointsCounter
        if startingPoints == "Locked":
            Utils.send_notification("🚫 Account is Locked", currentAccount["username"])
            return 0
        if startingPoints == "Verify":
            Utils.send_notification("❗️ Account needs to be verified", currentAccount["username"])
            return 0
        logging.info(
            f"[POINTS] You have {utils.formatNumber(accountPointsCounter)} points on your account"
        )
        DailySet(desktopBrowser).completeDailySet()
        PunchCards(desktopBrowser).completePunchCards()
        MorePromotions(desktopBrowser).completeMorePromotions()
        # VersusGame(desktopBrowser).completeVersusGame()
        (
            remainingSearches,
            remainingSearchesM,
        ) = utils.getRemainingSearches()

        # Introduce random pauses before and after searches
        pause_before_search = random.uniform(
            11.0, 15.0
        )  # Random pause between 11 to 15 seconds
        time.sleep(pause_before_search)

        if remainingSearches != 0:
            accountPointsCounter = Searches(desktopBrowser).bingSearches(
                remainingSearches
            )

        pause_after_search = random.uniform(
            11.0, 15.0
        )  # Random pause between 11 to 15 seconds
        time.sleep(pause_after_search)

        utils.goHome()
        goalPoints = utils.getGoalPoints()
        goalTitle = utils.getGoalTitle()

    if remainingSearchesM != 0:
        with Browser(mobile=True, account=currentAccount, args=args) as mobileBrowser:
            utils = mobileBrowser.utils
            accountPointsCounter = Login(mobileBrowser).login()
            accountPointsCounter = Searches(mobileBrowser).bingSearches(
                remainingSearchesM
            )

            utils.goHome()
            goalPoints = utils.getGoalPoints()
            goalTitle = utils.getGoalTitle()

    logging.info(
        f"[POINTS] You have earned {utils.formatNumber(accountPointsCounter - startingPoints)} points today !"
    )
    logging.info(
        f"[POINTS] You are now at {utils.formatNumber(accountPointsCounter)} points !"
    )
    goalNotifier = ""
    if goalPoints > 0:
        logging.info(
            f"[POINTS] You are now at {(utils.formatNumber((accountPointsCounter / goalPoints) * 100))}% of your goal ({goalTitle}) !\n"
        )
        goalNotifier = f"🎯 Goal reached: {(utils.formatNumber((accountPointsCounter / goalPoints) * 100))}% ({goalTitle})"

    Utils.send_notification(
        "Daily Points Update",
        "\n".join(
            [
                f"👤 Account: {currentAccount.get('username')}",
                f"⭐️ Points earned today: {utils.formatNumber(accountPointsCounter - startingPoints)}",
                f"💰 Total points: {utils.formatNumber(accountPointsCounter)}",
                goalNotifier,
            ]
        ),
    )

    return accountPointsCounter


def export_points_to_csv(points_data):
    logs_directory = Path(__file__).resolve().parent / "logs"
    csv_filename = logs_directory / "points_data.csv"
    with open(csv_filename, mode="a", newline="") as file:  # Use "a" mode for append
        fieldnames = ["Account", "Earned Points", "Points Difference"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Check if the file is empty, and if so, write the header row
        if file.tell() == 0:
            writer.writeheader()

        for data in points_data:
            writer.writerow(data)


# Define a function to load the previous day's points data from a file in the "logs" folder
def load_previous_points_data():
    logs_directory = Path(__file__).resolve().parent / "logs"
    try:
        with open(logs_directory / "previous_points_data.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


# Define a function to save the current day's points data for the next day in the "logs" folder
def save_previous_points_data(data):
    logs_directory = Path(__file__).resolve().parent / "logs"
    with open(logs_directory / "previous_points_data.json", "w") as file:
        json.dump(data, file, indent=4)


if __name__ == "__main__":
    main()
