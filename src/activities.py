import contextlib
import logging
from random import randint
from time import sleep

from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.browser import Browser
from src.constants import REWARDS_URL
from src.utils import CONFIG, sendNotification, getAnswerCode

def cleanupActivityTitle(activityTitle: str) -> str:
    return activityTitle.replace("\u200b", "").replace("\xa0", " ")

class Activities:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver

    def openDailySetActivity(self, cardId: int):
        # Count total number of cards
        total_cards = len(
            self.webdriver.find_elements(
                By.XPATH, '//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card'
            )
        )
        logging.info(f"Total number of Daily Set activity cards: {total_cards}.")

        cardId += 1
        element = self.webdriver.find_element(
            By.XPATH,
            f'//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[{cardId}]/div/card-content/mee-rewards-daily-set-item-content/div/a',
        )

        logging.info(f"Attempting to click on Daily Set activity card {cardId}.")
        # Perform Ctrl + Click (öffnet im neuen Tab)
        ActionChains(self.webdriver).key_down(Keys.CONTROL).click(element).key_up(Keys.CONTROL).perform()
        logging.info(f"Clicked on Daily Set activity card {cardId}.")

        logging.info(f"Marking card {cardId} as complete.")
        self.webdriver.execute_script("arguments[0].setAttribute('complete', 'true');", element)

        # We just switch to new tab, do NOT close it here
        new_windows = self.webdriver.window_handles
        if len(new_windows) > 1:
            self.webdriver.switch_to.window(new_windows[-1])
            logging.info(f"Switched to the new tab for card {cardId}.")
        else:
            logging.info(f"No new tab was opened for card {cardId}.")

    def openMorePromotionsActivity(self, cardId: int):
        cardId += 1
        element = self.webdriver.find_element(
            By.CSS_SELECTOR,
            f"#more-activities > .m-card-group > .ng-scope:nth-child({cardId}) .ds-card-sec",
        )
        self.browser.utils.click(element)
        new_windows = self.webdriver.window_handles
        if len(new_windows) > 1:
            self.webdriver.switch_to.window(new_windows[-1])

    def completeSearch(self):
        pass

    def completeSurvey(self):
        self.webdriver.find_element(By.ID, f"btoption{randint(0, 1)}").click()

    def completeQuiz(self):
        with contextlib.suppress(TimeoutException):
            startQuiz = self.browser.utils.waitUntilQuizLoads()
            self.browser.utils.click(startQuiz)
        self.browser.utils.waitUntilVisible(By.ID, "overlayPanel", 5)
        currentQuestionNumber: int = self.webdriver.execute_script(
            "return _w.rewardsQuizRenderInfo.currentQuestionNumber"
        )
        maxQuestions = self.webdriver.execute_script(
            "return _w.rewardsQuizRenderInfo.maxQuestions"
        )
        numberOfOptions = self.webdriver.execute_script(
            "return _w.rewardsQuizRenderInfo.numberOfOptions"
        )
        for _ in range(currentQuestionNumber, maxQuestions + 1):
            if numberOfOptions == 8:
                answers = []
                for i in range(numberOfOptions):
                    isCorrectOption = self.webdriver.find_element(
                        By.ID, f"rqAnswerOption{i}"
                    ).get_attribute("iscorrectoption")
                    if isCorrectOption and isCorrectOption.lower() == "true":
                        answers.append(f"rqAnswerOption{i}")
                for answer in answers:
                    element = self.webdriver.find_element(By.ID, answer)
                    self.browser.utils.click(element)
                    self.browser.utils.waitUntilQuestionRefresh()
            elif numberOfOptions in [2, 3, 4]:
                correctOption = self.webdriver.execute_script(
                    "return _w.rewardsQuizRenderInfo.correctAnswer"
                )
                for i in range(numberOfOptions):
                    if (
                        self.webdriver.find_element(
                            By.ID, f"rqAnswerOption{i}"
                        ).get_attribute("data-option")
                        == correctOption
                    ):
                        element = self.webdriver.find_element(By.ID, f"rqAnswerOption{i}")
                        self.browser.utils.click(element)
                        self.browser.utils.waitUntilQuestionRefresh()
                        break

    def completeABC(self):
        counter = self.webdriver.find_element(
            By.XPATH, '//*[@id="QuestionPane0"]/div[2]'
        ).text[:-1][1:]
        numberOfQuestions = max(int(s) for s in counter.split() if s.isdigit())
        for question in range(numberOfQuestions):
            element = self.webdriver.find_element(
                By.ID, f"questionOptionChoice{question}{randint(0, 2)}"
            )
            self.browser.utils.click(element)
            sleep(randint(10, 15))
            element = self.webdriver.find_element(By.ID, f"nextQuestionbtn{question}")
            self.browser.utils.click(element)
            sleep(randint(10, 15))

    def completeThisOrThat(self):
        startQuiz = self.browser.utils.waitUntilQuizLoads()
        self.browser.utils.click(startQuiz)
        self.browser.utils.waitUntilVisible(
            By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 10
        )
        sleep(randint(10, 15))
        for _ in range(10):
            correctAnswerCode = self.webdriver.execute_script(
                "return _w.rewardsQuizRenderInfo.correctAnswer"
            )
            answer1, answer1Code = self.getAnswerAndCode("rqAnswerOption0")
            answer2, answer2Code = self.getAnswerAndCode("rqAnswerOption1")
            if answer1Code == correctAnswerCode:
                answerToClick = answer1
            else:
                answerToClick = answer2
            self.browser.utils.click(answerToClick)
            sleep(randint(10, 15))

    def getAnswerAndCode(self, answerId: str) -> tuple[WebElement, str]:
        answerEncodeKey = self.webdriver.execute_script("return _G.IG")
        answer = self.webdriver.find_element(By.ID, answerId)
        answerTitle = answer.get_attribute("data-option")
        return (
            answer,
            getAnswerCode(answerEncodeKey, answerTitle),
        )

    def doActivity(self, activity: dict, activities: list[dict]) -> None:
        try:
            activityTitle = cleanupActivityTitle(activity["title"])
            logging.info(f"Processing activity: {activityTitle}")

            # Abbrechen, wenn schon done oder 0 Punkt
            if activity["complete"] is True or activity["pointProgressMax"] == 0:
                logging.info("Activity already completed. Skipping.")
                return

            # Apprise-Check
            apprise_conf = CONFIG.get("apprise")
            ignore_list = []
            if isinstance(apprise_conf, dict):
                notify_conf = apprise_conf.get("notify", {})
                incomp_conf = notify_conf.get("incomplete-activity", {})
                if isinstance(incomp_conf, dict):
                    ignore_list = incomp_conf.get("ignore", [])

            if activityTitle in ignore_list:
                logging.info(f"Ignoring activity: {activityTitle}")
                return

            cardId = activities.index(activity)
            isDailySet = (
                "daily_set_date" in activity["attributes"]
                and activity["attributes"]["daily_set_date"]
            )

            # Öffnet das neue Tab, nicht schließen
            if isDailySet:
                self.openDailySetActivity(cardId)
            else:
                self.openMorePromotionsActivity(cardId)

            try:
                # Warte auf Suchfeld, falls vorhanden
                with contextlib.suppress(TimeoutException):
                    searchbar = self.browser.utils.waitUntilClickable(By.ID, "sb_form_q", 10)
                    if searchbar:
                        self.browser.utils.click(searchbar)

                # Falls Title in config.yaml -> Suchen
                if (
                    hasattr(CONFIG, 'activities') 
                    and hasattr(CONFIG.activities, 'search')
                    and activityTitle in CONFIG.activities.search
                ):
                    to_search = CONFIG.activities.search[activityTitle]
                    searchbar.send_keys(to_search)
                    sleep(2)
                    searchbar.submit()

                elif "poll" in activityTitle.lower():
                    logging.info(f"[ACTIVITY] Completing poll for card {cardId}")
                    self.completeSurvey()

                elif activity["promotionType"] == "urlreward":
                    self.completeSearch()

                elif activity["promotionType"] == "quiz":
                    # Hier rufen wir die verschiedenen Quiz-Funktionen auf
                    if activity["pointProgressMax"] == 10:
                        self.completeABC()
                    elif activity["pointProgressMax"] in [30, 40]:
                        self.completeQuiz()
                    elif activity["pointProgressMax"] == 50:
                        self.completeThisOrThat()

                else:
                    self.completeSearch()

            except Exception as e:
                logging.error(f"Error while handling activity {activityTitle}: {e}")

        except Exception as e:
            logging.error(f"[ACTIVITY] Error processing activity {activityTitle}: {e}", exc_info=True)

        #
        # --> NACH dem Quiz/Survey/etc. jetzt den Tab schließen.
        #
        all_windows = self.webdriver.window_handles
        if len(all_windows) > 1:
            # Schließe das aktuelle (letzte) Tab
            self.webdriver.close()
            # Wechsle zurück zum ersten Tab
            self.webdriver.switch_to.window(all_windows[0])

        sleep(randint(2, 5))
        logging.info("Resetting tabs.")
        self.browser.utils.resetTabs()
        logging.info("Finished processing activity.")

    def completeActivities(self):
        logging.info("[DAILY SET] Trying to complete the Daily Set...")
        dailySetPromotions = self.browser.utils.getDailySetPromotions()
        self.browser.utils.goToRewards()
        for activity in dailySetPromotions:
            self.doActivity(activity, dailySetPromotions)
        logging.info("[DAILY SET] Done")

        logging.info("[MORE PROMOS] Trying to complete More Promotions...")
        morePromotions = self.browser.utils.getMorePromotions()
        self.browser.utils.goToRewards()
        for activity in morePromotions:
            self.doActivity(activity, morePromotions)
        logging.info("[MORE PROMOS] Done")

        # todo Send one email for all accounts?
        # fixme This is falsely considering some activities incomplete when complete
        apprise_conf = CONFIG.get("apprise")
        if isinstance(apprise_conf, dict):
            notify_conf = apprise_conf.get("notify", {})
            incomp_conf = notify_conf.get("incomplete-activity", {})
            if isinstance(incomp_conf, dict) and incomp_conf.get("enabled"):
                incompleteActivities: dict[str, tuple[str, str, str]] = {}
                for activity in (
                    self.browser.utils.getDailySetPromotions()
                    + self.browser.utils.getMorePromotions()
                ):
                    if activity["pointProgress"] < activity["pointProgressMax"]:
                        incompleteActivities[cleanupActivityTitle(activity["title"])] = (
                            activity["promotionType"],
                            activity["pointProgress"],
                            activity["pointProgressMax"],
                        )
                if hasattr(CONFIG, 'activities') and hasattr(CONFIG.activities, 'ignore'):
                    for incompleteActivityToIgnore in CONFIG.activities.ignore:
                        incompleteActivities.pop(incompleteActivityToIgnore, None)

                if incompleteActivities:
                    logging.info(f"incompleteActivities: {incompleteActivities}")
                    sendNotification(
                        f"We found some incomplete activities for {self.browser.email}",
                        str(incompleteActivities) + "\n" + REWARDS_URL,
                    )
