import contextlib
import dbm.dumb
import json
import logging
import random
import shelve
import time
from datetime import date, timedelta
from enum import Enum, auto
from itertools import cycle
from typing import Final
import requests
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from src.browser import Browser
from src.utils import Utils

LOAD_DATE_KEY = "loadDate"
with open("session_recall.txt", "r") as file:
    allText = file.read()
    words = list(map(str, allText.split()))
    random.shuffle(words)

class RetriesStrategy(Enum):
    EXPONENTIAL = auto()
    CONSTANT = auto()
class Searches:
    config = Utils.loadConfig()
    maxRetries: Final[int] = config.get("retries", {}).get("max", 3)
    baseDelay: Final[float] = config.get("retries", {}).get("base_delay_in_seconds", 5)
    retriesStrategy = RetriesStrategy[config.get("retries", {}).get("strategy", RetriesStrategy.CONSTANT.name)]
    def __init__(self, browser: Browser):
        self.counter = 0
        #self.maxCounter = 0
        self.browser = browser
        self.webdriver = browser.webdriver
        dumbDbm = dbm.dumb.open((Utils.getProjectRoot() / "google_trends").__str__())
        self.googleTrendsShelf: shelve.Shelf = shelve.Shelf(dumbDbm)
        logging.debug(f"google_trends = {list(self.googleTrendsShelf.items())}")
        loadDate: date | None = None
        if LOAD_DATE_KEY in self.googleTrendsShelf:
            loadDate = self.googleTrendsShelf[LOAD_DATE_KEY]
        if loadDate is None or loadDate < date.today():
            self.googleTrendsShelf.clear()
            trends = self.getGoogleTrends(browser.getRemainingSearches(desktopAndMobile=True).getTotal())
            random.shuffle(trends)
            for trend in trends:
                self.googleTrendsShelf[trend] = None
            self.googleTrendsShelf[LOAD_DATE_KEY] = date.today()
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.googleTrendsShelf.__exit__(None, None, None)
    def getGoogleTrends(self, wordsCount: int) -> list[str]:
        searchTerms: list[str] = []
        i = 0

        session = Utils.makeRequestsSession()
        while len(searchTerms) < wordsCount:
            i += 1
            r = session.get(
                f"https://trends.google.com/trends/api/dailytrends?hl={self.browser.localeLang}"
                f'&ed={(date.today() - timedelta(days=i)).strftime("%Y%m%d")}&geo={self.browser.localeGeo}&ns=15')
            assert r.status_code == requests.codes.ok
            trends = json.loads(r.text[6:])
            for topic in trends["default"]["trendingSearchesDays"][0]["trendingSearches"]:
                searchTerms.append(topic["title"]["query"].lower())
                searchTerms.extend(relatedTopic["query"].lower()
                    for relatedTopic in topic["relatedQueries"])
            searchTerms = list(set(searchTerms))
        del searchTerms[wordsCount : (len(searchTerms) + 1)]
        return searchTerms

    def getRelatedTerms(self, term: str) -> list[str]:
        relatedTerms: list[str] = requests.get(
            f"https://bing.com/osjson.aspx?query={term}",
            headers={"User-agent": self.browser.userAgent},).json()[1]
        if not relatedTerms:
            return [term]
        return relatedTerms

    def bingSearches(self) -> None:
        logging.info(f"Starting {self.browser.browserType.capitalize()} Edge Bing searches...")
        self.browser.utils.goToSearch()
        remainingSearches = self.browser.getRemainingSearches()
        for searchCount in range(1, remainingSearches + 1):
            pointsAfter = self.browser.utils.getAccountPoints()
            logging.info(f"{searchCount}/{remainingSearches}"+ f"  Current Balance: {pointsAfter}")
            self.bingSearch()
            time.sleep(0.05)
        logging.info(f"Finished {self.browser.browserType.capitalize()} Edge Bing searches !")
        logging.info("Going into Mobile.")

    def bingSearch(self) -> None:
        pointsBefore = self.browser.utils.getAccountPoints()
        rootTerm = list(self.googleTrendsShelf.keys())[0]
        terms = self.getRelatedTerms(rootTerm)
        termsCycle: cycle[str] = cycle(terms)
        baseDelay = Searches.baseDelay
        for i in range(self.maxRetries + 1):
            if i != 0:
                sleepTime: float
                if Searches.retriesStrategy == Searches.retriesStrategy.EXPONENTIAL:
                    sleepTime = baseDelay * 2 ** (i - 1)
                elif Searches.retriesStrategy == Searches.retriesStrategy.CONSTANT:
                    sleepTime = baseDelay
                else:
                    raise AssertionError

                logging.debug(f"Search attempt failed {i}/{Searches.maxRetries}, sleeping {sleepTime}"f" seconds")
                pointsAfter = self.browser.utils.getAccountPoints()
                self.counter += 1
                #remainingSearches = self.browser.getRemainingSearches()
                logging.info(f"Balance: {pointsAfter} "+f" failed Attempts: {self.counter}")# +f" max limited search-round Attempts: {self.maxCounter} "+f" remaining searches in Total: {remainingSearches}")
                time.sleep(sleepTime)

        searchbar = self.browser.utils.waitUntilClickable(By.ID, "sb_form_q", timeToWait=40)
        for _ in range(1000):
                self.browser.utils.click(searchbar)
                searchbar.clear()
                term = next(termsCycle,random.choice(words))
                self.browser.utils.click(searchbar)
                searchbar.send_keys(term)
                searchbar.submit()
                logging.info(f"Search:  {term}")
                with contextlib.suppress(TimeoutException):
                    WebDriverWait(self.webdriver,15).until(expected_conditions.text_to_be_present_in_element_value((By.ID, "sb_form_q"), term))
                    break
                logging.debug("error send_keys")


        else:
            raise TimeoutException

        pointsAfter = self.browser.utils.getAccountPoints()

        if pointsAfter==(pointsBefore + 3):
            time.sleep(0.05)
           # if self.maxCounter >=1:
            #    self.maxCounter -=1
            #remainingSearches = self.browser.getRemainingSearches()
            logging.info("3 Points received! "+f"Balance: {pointsAfter} "+f"failed Attempts: {self.counter}")# +f" max limited search-round Attempts: {self.maxCounter} "+f" remaining searches in Total: {remainingSearches}")
            return
        logging.error("Reached max retry attempts!")
        #self.maxCounter += 1
        logging.debug(f"Failed search Attempts in Total: {self.counter}")# max limited search-round Attempts: {self.maxCounter}")
        del self.googleTrendsShelf[rootTerm]
      #  if self.maxCounter == 12:
          #  logging.info("*"*44)
           # logging.debug(f"Limited Attempts reached: {self.maxCounter}, next Account will go on")
           # logging.info("*"*44)
           # self.webdriver.close()
          #  self.webdriver.quit()
         #   return
