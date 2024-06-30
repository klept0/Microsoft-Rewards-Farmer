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
from selenium.webdriver.common.by import By

from src.browser import Browser
from src.utils import Utils, RemainingSearches

LOAD_DATE_KEY = "loadDate"


class AttemptsStrategy(Enum):
    exponential = auto()
    constant = auto()


class Searches:
    config = Utils.loadConfig()
    maxAttempts: Final[int] = config.get("attempts", {}).get("max", 6)
    baseDelay: Final[float] = config.get("attempts", {}).get(
        "base_delay_in_seconds", 60
    )
    # attemptsStrategy = Final[  # todo Figure why doesn't work with equality below
    attemptsStrategy = AttemptsStrategy[
        config.get("attempts", {}).get("strategy", AttemptsStrategy.constant.name)
    ]

    def __init__(self, browser: Browser, searches: RemainingSearches):
        self.browser = browser
        self.webdriver = browser.webdriver

        self.googleTrendsShelf: shelve.Shelf = shelve.open(
            (Utils.getProjectRoot() / "google_trends").__str__()
        )
        logging.debug(f"googleTrendsShelf.__dict__ = {self.googleTrendsShelf.__dict__}")
        logging.debug(f"google_trends = {list(self.googleTrendsShelf.items())}")
        loadDate: date | None = None
        if LOAD_DATE_KEY in self.googleTrendsShelf:
            loadDate = self.googleTrendsShelf[LOAD_DATE_KEY]

        if loadDate is None or loadDate < date.today():
            self.googleTrendsShelf.clear()
            self.googleTrendsShelf[LOAD_DATE_KEY] = date.today()
            trends = self.getGoogleTrends(searches.getTotal())
            random.shuffle(trends)
            for trend in trends:
                self.googleTrendsShelf[trend] = None
            logging.debug(
                f"google_trends after load = {list(self.googleTrendsShelf.items())}"
            )

    def getGoogleTrends(self, wordsCount: int) -> list[str]:
        # Function to retrieve Google Trends search terms
        searchTerms: list[str] = []
        i = 0
        while len(searchTerms) < wordsCount:
            i += 1
            # Fetching daily trends from Google Trends API
            r = requests.get(
                f"https://trends.google.com/trends/api/dailytrends?hl={self.browser.localeLang}"
                f'&ed={(date.today() - timedelta(days=i)).strftime("%Y%m%d")}&geo={self.browser.localeGeo}&ns=15'
            )
            trends = json.loads(r.text[6:])
            for topic in trends["default"]["trendingSearchesDays"][0][
                "trendingSearches"
            ]:
                searchTerms.append(topic["title"]["query"].lower())
                searchTerms.extend(
                    relatedTopic["query"].lower()
                    for relatedTopic in topic["relatedQueries"]
                )
            searchTerms = list(set(searchTerms))
        del searchTerms[wordsCount : (len(searchTerms) + 1)]
        return searchTerms

    def getRelatedTerms(self, term: str) -> list[str]:
        # Function to retrieve related terms from Bing API
        relatedTerms: list[str] = requests.get(
            f"https://api.bing.com/osjson.aspx?query={term}",
            headers={"User-agent": self.browser.userAgent},
        ).json()[1]
        if not relatedTerms:
            return [term]
        return relatedTerms

    def bingSearches(self, numberOfSearches: int, pointsCounter: int = 0) -> int:
        # Function to perform Bing searches
        logging.info(
            f"[BING] Starting {self.browser.browserType.capitalize()} Edge Bing searches..."
        )

        self.browser.utils.goToSearch()

        # todo Make sure rewards quiz is done

        for searchCount in range(1, numberOfSearches + 1):
            # todo Disable cooldown for first 3 searches (Earning starts with your third search)
            logging.info(f"[BING] {searchCount}/{numberOfSearches}")
            googleTrends: list[str] = list(self.googleTrendsShelf.keys())
            logging.debug(f"self.googleTrendsShelf.keys() = {googleTrends}")
            googleTrend = list(self.googleTrendsShelf.keys())[1]
            pointsCounter = self.bingSearch(googleTrend)
            logging.debug(f"pointsCounter = {pointsCounter}")
            time.sleep(random.randint(10, 15))

        logging.info(
            f"[BING] Finished {self.browser.browserType.capitalize()} Edge Bing searches !"
        )
        self.googleTrendsShelf.close()
        return pointsCounter

    def bingSearch(self, term: str) -> int:
        # Function to perform a single Bing search
        pointsBefore = self.browser.utils.getAccountPoints()

        terms = self.getRelatedTerms(term)
        logging.debug(f"terms={terms}")
        termsCycle: cycle[str] = cycle(terms)
        baseDelay = Searches.baseDelay
        passedInTerm = term
        logging.debug(f"passedInTerm={passedInTerm}")

        for i in range(self.maxAttempts):
            try:
                searchbar = self.browser.utils.waitUntilVisible(
                    By.ID, "sb_form_q", timeToWait=20
                )
            catch:
                logging.debug('Exception in: searchbar = self.browser.utils.waitUntilVisible')
                continue
            
            for _ in range(100):
                searchbar.clear()
                term = next(termsCycle)
                logging.debug(f"term={term}")
                searchbar.send_keys(term)
                time.sleep(4)
                try:
                    assert searchbar.get_attribute("value") == term
                except AssertionError:
                    logging.debug('searchbar.get_attribute("value") != term')
                    continue
                break

            searchbar.submit()

            pointsAfter = self.browser.utils.getAccountPoints()
            if pointsBefore < pointsAfter:
                del self.googleTrendsShelf[passedInTerm]
                return pointsAfter

            # todo
            # if i == (maxAttempts / 2):
            #     logging.info("[BING] " + "TIMED OUT GETTING NEW PROXY")
            #     self.webdriver.proxy = self.browser.giveMeProxy()

            baseDelay += random.randint(1, 10)  # add some jitter
            logging.debug(
                f"[BING] Search attempt failed {i + 1}/{Searches.maxAttempts}, retrying after sleeping {baseDelay}"
                f" seconds..."
            )
            time.sleep(baseDelay)

            if Searches.attemptsStrategy == AttemptsStrategy.exponential:
                baseDelay *= 2
        # todo debug why we get to this point occasionally even though searches complete
        # update - Seems like account points aren't refreshing correctly see
        logging.error("[BING] Reached max search attempt retries")

        logging.debug("Moving passedInTerm to end of list")
        del self.googleTrendsShelf[passedInTerm]
        self.googleTrendsShelf[passedInTerm] = None

        return pointsBefore
