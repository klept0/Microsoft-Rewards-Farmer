import contextlib
import logging
import random
import time

from selenium.common import TimeoutException
from selenium.webdriver.common.by import By

from src.browser import Browser
from .activities import Activities
from .utils import Utils



class MorePromotions:


    def __init__(self, browser: Browser):
        self.browser = browser
        self.activities = Activities(browser)
        self.webdriver = browser.webdriver

    def completeMorePromotions(self):
        logging.info("[MORE PROMOS] " + "Trying to complete More Promotions...")
        morePromotions: list[dict] = self.browser.utils.getDashboardData()["morePromotions"]
        self.browser.utils.goToRewards()
        for promotion in morePromotions:
            try:
                promotionTitle = promotion["title"].replace("\u200b", "").replace("\xa0", " ")
                logging.debug(f"promotionTitle={promotionTitle}")
                # Open the activity for the promotion
                if (promotion["complete"] is not False
                    or promotion["pointProgressMax"] == 0):
                    logging.debug("Already done, continuing")
                    continue

                pointsBefore = self.browser.utils.getAccountPoints()
                self.activities.openMorePromotionsActivity(morePromotions.index(promotion))
                self.browser.webdriver.execute_script("window.scrollTo(0, 1080)")
                with contextlib.suppress(TimeoutException):
                    searchbar = self.browser.utils.waitUntilClickable(By.ID, "sb_form_q")
                    searchbar.click()
                    searchbar.clear() #Add
                if "Search the lyrics of a song" in promotionTitle:
                    keys = "black sabbath supernaut lyrics"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Translate anything" in promotionTitle:
                    keys = "translate pencil sharpener to spanish"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Planen Sie einen Kurztrip" in promotionTitle:
                    keys ="find me a flight"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Entdecken Sie freie Stellen" in promotionTitle:
                    keys = "find me jobs in my area"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Die Kunst von Cézanne" in promotionTitle:
                    keys = "Cézanne Art"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Stein für Stein" in promotionTitle:
                    keys = "Stick and Stones"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Wie spät ist es?" in promotionTitle:
                    keys = "What time is it"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Naturwunder" in promotionTitle:
                    keys = "Torres del Paine Nationalpark"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Zeit zum Spielen" in promotionTitle:
                    keys = "Call of Duty"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Wer hat gewonnen?" in promotionTitle:
                    keys = "Fc bayern"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Erweitern Sie Ihr Vokabular" in promotionTitle:
                    keys = "Was bedeutet wortschatz"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Bleiben Sie bezüglich der Wahlen auf dem Laufenden" in promotionTitle:
                    keys = "elections"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Suchen Sie einen Liedtext" in promotionTitle:
                    keys = "Lyrics Mona Lisa"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Filmbegriffe" in promotionTitle:
                    keys = "Was ist eine lange Einstellung im Film?"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Naturwunder" in promotionTitle:
                    keys = "Torres del Paine Nationalpark"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Machen Sie die Tour" in promotionTitle:
                    keys = "Do a Tour"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Kunstwerke am Strand" in promotionTitle:
                    keys = "So geht Sandkunst"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Take the tour" in promotionTitle:
                    keys = "Tour Planing and taking"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Diesen Film noch einmal anschauen" in promotionTitle:
                    keys = "Spiderman Movie"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Let's watch that movie again" in promotionTitle:
                    keys = "watch aliens movie"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Discover open job roles" in promotionTitle:
                    keys = "walmart open job roles"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Plan a quick getaway" in promotionTitle:
                    keys = "flights nyc to paris"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "You can track your package" in promotionTitle:
                    keys = "usps tracking"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Jennifer Lopez-Bewunderer?" in promotionTitle:
                    keys = "Bing Jennifer Lopez-Quiz"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Übersetzen Sie etwas!" in promotionTitle:
                    keys = "Translate Transe"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Find somewhere new to explore" in promotionTitle:
                    keys = "directions to new york"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Too tired to cook tonight?" in promotionTitle:
                    keys = "mcdonalds"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Ganzheitliche Vorteile" in promotionTitle:
                    keys = "Akupunktur"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Quickly convert your money" in promotionTitle:
                    keys = "convert 325 usd to yen"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif "Learn to cook a new recipe" in promotionTitle:
                    keys = "how cook pierogi"
                    searchbar.send_keys(f"{keys}")
                    searchbar.submit()
                elif promotion["promotionType"] == "urlreward":
                    # Complete search for URL reward
                    self.activities.completeSearch()
                elif (promotion["promotionType"] == "quiz"
                    and promotion["pointProgress"] == 0):
                    # Complete different types of quizzes based on point progress max
                    if promotion["pointProgressMax"] == 10:
                        self.activities.completeABC()
                    elif promotion["pointProgressMax"] in [30, 40]:
                        self.activities.completeQuiz()
                    elif promotion["pointProgressMax"] == 50:
                        self.activities.completeThisOrThat()
                else:
                    # Default to completing search
                    self.activities.completeSearch()
                self.browser.webdriver.execute_script("window.scrollTo(0, 1080)")
                time.sleep(0.15)
                logging.info(f"[IS_DOING]:{promotionTitle}")
                #logging.info("Sending:   → "+f"{keys}"+" ←")
                time.sleep(12)
                pointsAfter = self.browser.utils.getAccountPoints()
                time.sleep(0.35)
                if pointsBefore != pointsAfter:
                    pointsNow = self.browser.utils.getAccountPoints()
                    pointsGot = pointsNow - pointsBefore
                    logging.info(f"You have received {pointsGot} Points!"+" "+"Current Balance is now:"+" "+f"{pointsAfter}")
                    if pointsGot == 3:
                        logging.error(f"(3) Could not complete:   {promotionTitle}  - GO NEXT")
                        return
                    if pointsGot == 0:
                        logging.error(f"(0) Can't complete Promotion!:   {promotionTitle}  - GO NEXT")
                        return
            except Exception:

                time.sleep(0.1)
                logging.error(f"(I) INCOMPLETE PROMOTION : {promotionTitle}  - GO NEXT")
                logging.error("Can't complete Promotion!")
                time.sleep(0.05)
                self.browser.utils.resetTabs()
                continue

        logging.info("EXIT PROMOS - GOING TO BING SEARCH!\n")
