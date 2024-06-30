import logging

from src.browser import Browser
from .activities import Activities


# todo Rename MoreActivities?
class MorePromotions:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.activities = Activities(browser)

    def completeMorePromotions(self):
        # Function to complete More Promotions
        logging.info("[MORE PROMOS] " + "Trying to complete More Promotions...")
        morePromotions: list[dict] = self.browser.utils.getDashboardData()[
            "morePromotions"
        ]
        self.browser.utils.goToRewards()
        for promotion in morePromotions:
            try:
                promotionTitle = promotion["title"]
                logging.debug(f"promotionTitle={promotionTitle}")
                # Open the activity for the promotion
                if (
                    promotion["complete"] is not False
                    or promotion["pointProgressMax"] == 0
                ):
                    logging.debug("Already done, continuing")
                    # todo Handle special "Quote of the day" which is falsely complete
                    continue
                self.activities.openMorePromotionsActivity(
                    morePromotions.index(promotion)
                )
                if promotion["promotionType"] == "urlreward":
                    if promotion["title"] == "Search the lyrics of a song":
                        self.browser.webdriver.get(
                            "https://www.bing.com/search?q=black+sabbath+supernaut+lyrics"
                        )
                    elif promotion["title"] == "Translate anything":
                        self.browser.webdriver.get(
                            "https://www.bing.com/search?q=translate+pencil+sharpener+to+spanish"
                        )
                    # Complete search for URL reward
                    self.activities.completeSearch()
                elif (
                    promotion["promotionType"] == "quiz"
                    and promotion["pointProgress"] == 0
                ):
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
            except Exception:  # pylint: disable=broad-except
                logging.error("[MORE PROMOS] Error More Promotions", exc_info=True)
                # Reset tabs in case of an exception
                self.browser.utils.resetTabs()
                continue
        logging.info("[MORE PROMOS] Exiting")
