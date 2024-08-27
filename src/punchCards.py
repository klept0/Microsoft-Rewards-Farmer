import logging
import random
import time
import urllib.parse

from selenium.webdriver.common.by import By

from src.browser import Browser
from .constants import REWARDS_URL


class PunchCards:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver

    def completePunchCard(self, url: str, childPromotions: dict):
        self.webdriver.get(url)
        for child in childPromotions:
            if child["complete"] is False:
                if child["promotionType"] == "urlreward":
                    self.webdriver.find_element(By.XPATH, "//a[@class='offer-cta']/div").click()
                    self.browser.utils.visitNewTab(10)
                if child["promotionType"] == "quiz":
                    self.webdriver.find_element(By.XPATH, "//a[@class='offer-cta']/div").click()
                    self.browser.utils.switchToNewTab(3)
                    counter = str(self.webdriver.find_element(By.XPATH, '//*[@id="QuestionPane0"]/div[2]').get_attribute("innerHTML"))[:-1][1:]
                    numberOfQuestions = max(int(s) for s in counter.split() if s.isdigit())
                    for question in range(numberOfQuestions):
                        self.webdriver.find_element(By.XPATH,f'//*[@id="QuestionPane{question}"]/div[1]/div[2]/a[{random.randint(1, 3)}]/div',).click()
                        time.sleep(0.05)
                        self.webdriver.find_element(By.XPATH,f'//*[@id="AnswerPane{question}"]/div[1]/div[2]/div[4]/a/div/span/input',).click()
                        time.sleep(0.05)
                    self.browser.utils.closeCurrentTab()


    def completePunchCards(self):
        logging.info("[PUNCH CARDS] " + "Trying to complete the Punch Cards...")
        self.completePromotionalItems()
        punchCards = self.browser.utils.getDashboardData()["punchCards"]
        self.browser.utils.goToRewards()
        for punchCard in punchCards:
            try:
                if (punchCard["parentPromotion"]
                    and punchCard["childPromotions"]
                    and not punchCard["parentPromotion"]["complete"]
                    and punchCard["parentPromotion"]["pointProgressMax"] != 0):
                    # Complete each punch card
                    self.completePunchCard(punchCard["parentPromotion"]["attributes"]["destination"],punchCard["childPromotions"],)

                    self.webdriver.find_element(By.XPATH,
                                                "//div[@id=\'daily-sets\']/mee-card-group/div/mee-card/div/card-content/mee-rewards-daily-set-item-content/div/a/div[2]/p").click()
                    self.browser.utils.goToRewards()
                    self.webdriver.find_element(By.XPATH,
                                                "//div[@id=\'daily-sets\']/mee-card-group/div/mee-card/div/card-content/mee-rewards-daily-set-item-content/div/a").click()
                    self.browser.utils.goToRewards()
                    self.webdriver.find_element(By.XPATH,
                                                "//mee-card[3]/div/card-content/mee-rewards-daily-set-item-content/div/a/div[2]/h3").click()
                    self.browser.utils.goToRewards()

            except Exception:  # pylint: disable=broad-except
                logging.error("[PUNCH CARDS] Error Punch Cards", exc_info=True)
                self.browser.utils.resetTabs()
                continue
        logging.info("[PUNCH CARDS] Exiting")
    def completePromotionalItems(self):
        try:
            item = self.browser.utils.getDashboardData()["promotionalItem"]
            self.browser.utils.goToRewards()
            destUrl = urllib.parse.urlparse(item["destinationUrl"])          #(item["destinationUrl"])
            baseUrl = urllib.parse.urlparse(REWARDS_URL)

            if ((item["pointProgressMax"] in [100, 200, 500])
                and not item["complete"]
                and ((destUrl.hostname == baseUrl.hostname
                        and destUrl.path == baseUrl.path)
                    or destUrl.hostname == "www.bing.com")):
                self.webdriver.find_element(By.XPATH, '//*[@id="promo-item"]/section/div/div/div/span').click()
                self.browser.utils.visitNewTab(1)
        except Exception:
            logging.debug("", exc_info=True)
