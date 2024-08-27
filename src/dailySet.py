import logging
import time
import urllib.parse
from datetime import datetime

from src.browser import Browser
from .activities import Activities

class DailySet:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.activities = Activities(browser)
    def completeDailySet(self):
        logging.info("[DAILY SET] " + "Trying to complete the Daily Set...")
        data = self.browser.utils.getDashboardData()["dailySetPromotions"]
        self.browser.utils.goToRewards()
        self.activities.dashboardPopUpModalCloseCross()



        todayDate = datetime.now().strftime("%m/%d/%Y")
        for activity in data.get(todayDate, []):
            cardId = int(activity["offerId"][-1:])
            try:
                if activity["complete"] is not False:
                    continue

                self.activities.openDailySetActivity(cardId)

                if activity["promotionType"] == "urlreward":
                    logging.info(f"[DAILY SET] Completing search of card {cardId}")
                    self.activities.completeSearch()
                if activity["promotionType"] == "quiz":
                    if (activity["pointProgressMax"] == 50
                        and activity["pointProgress"] == 0):
                        logging.info("[DAILY SET] " + f"Completing This or That of card {cardId}")
                        self.activities.completeThisOrThat()
                    elif (activity["pointProgressMax"] in [40, 30]
                        and activity["pointProgress"] == 0):
                        logging.info(f"[DAILY SET] Completing quiz of card {cardId}")
                        self.activities.completeQuiz()
                    elif (activity["pointProgressMax"] == 10
                        and activity["pointProgress"] == 0):
                        # Extract and parse search URL for additional checks
                        searchUrl = urllib.parse.unquote(urllib.parse.parse_qs(urllib.parse.urlparse(activity["destinationUrl"]).query)["ru"][0])
                        searchUrlQueries = urllib.parse.parse_qs(urllib.parse.urlparse(searchUrl).query)
                        filters = {}
                        for filterEl in searchUrlQueries["filters"][0].split(" "):
                            filterEl = filterEl.split(":", 1)
                            filters[filterEl[0]] = filterEl[1]
                        if "PollScenarioId" in filters:
                            logging.info(f"[DAILY SET] Completing poll of card {cardId}")
                            self.activities.completeSurvey()
                        else:
                            logging.info(f"[DAILY SET] Completing quiz of card {cardId}")
                            try:
                                self.activities.completeABC()
                            except Exception:
                                logging.warning("", exc_info=True)
                                self.activities.completeQuiz()
            except Exception:
                logging.error(f"[DAILY SET] Error Daily Set of card {cardId}", exc_info=True)
                # Reset tabs in case of an exception
                self.browser.utils.resetTabs()
                continue

        logging.info("[DAILY SET] Exiting")
