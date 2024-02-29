import contextlib
import logging
import time
import urllib.parse

from selenium.webdriver.common.by import By

from src.browser import Browser


class Login:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.utils = browser.utils

    def login(self):
        logging.info("[LOGIN] " + "Logging-in...")
        self.webdriver.get(
            "https://rewards.bing.com/Signin/"
        )  # changed site to allow bypassing when M$ blocks access to login.live.com randomly
        alreadyLoggedIn = False
        while True:
            try:
                self.utils.waitUntilVisible(
                    By.CSS_SELECTOR, 'html[data-role-name="RewardsPortal"]', 0.1
                )
                alreadyLoggedIn = True
                break
            except Exception:  # pylint: disable=broad-except
                try:
                    self.utils.waitUntilVisible(By.ID, "i0116", 10)
                    break
                except Exception:  # pylint: disable=broad-except
                    if self.utils.tryDismissAllMessages():
                        continue

        if not alreadyLoggedIn:
            if isLocked := self.executeLogin():
                return "Locked"
        self.utils.tryDismissCookieBanner()

        logging.info("[LOGIN] " + "Logged-in !")

        self.utils.goHome()
        points = self.utils.getAccountPoints()

        logging.info("[LOGIN] " + "Ensuring you are logged into Bing...")
        self.checkBingLogin()
        logging.info("[LOGIN] Logged-in successfully !")
        return points

    def executeLogin(self):
        self.utils.waitUntilVisible(By.ID, "i0116", 10)
        logging.info("[LOGIN] " + "Entering email...")
        self.utils.waitUntilClickable(By.NAME, "loginfmt", 10)
        email_field = self.webdriver.find_element(By.NAME, "loginfmt")

        while True:
            email_field.send_keys(self.browser.username)
            time.sleep(3)
            if email_field.get_attribute("value") == self.browser.username:
                self.webdriver.find_element(By.ID, "idSIButton9").click()
                break

            email_field.clear()
            time.sleep(3)

        try:
            self.enterPassword(self.browser.password)
        except Exception:  # pylint: disable=broad-except
            logging.error("[LOGIN] " + "2FA Code required !")
            with contextlib.suppress(Exception):
                code = self.webdriver.find_element(
                    By.ID, "idRemoteNGC_DisplaySign"
                ).get_attribute("innerHTML")
                logging.error(f"[LOGIN] 2FA code: {code}")
            logging.info("[LOGIN] Press enter when confirmed on your device...")
            input()

        while not (
            urllib.parse.urlparse(self.webdriver.current_url).path == "/"
            and urllib.parse.urlparse(self.webdriver.current_url).hostname
            == "account.microsoft.com"
        ):
            if urllib.parse.urlparse(self.webdriver.current_url).hostname == "rewards.bing.com":
                self.webdriver.get("https://account.microsoft.com")
            
            if "Abuse" in str(self.webdriver.current_url):
                logging.error(f"[LOGIN] {self.browser.username} is locked")
                return True
            self.utils.tryDismissAllMessages()
            time.sleep(1)

        self.utils.waitUntilVisible(
            By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 10
        )

    def enterPassword(self, password):
        self.utils.waitUntilClickable(By.NAME, "passwd", 10)
        self.utils.waitUntilClickable(By.ID, "idSIButton9", 10)
        # browser.webdriver.find_element(By.NAME, "passwd").send_keys(password)
        # If password contains special characters like " ' or \, send_keys() will not work
        password = password.replace("\\", "\\\\").replace('"', '\\"')

        logging.info("[LOGIN] " + "Writing password...")

        password_field = self.webdriver.find_element(By.NAME, "passwd")

        while True:
            password_field.send_keys(password)
            time.sleep(3)
            if password_field.get_attribute("value") == password:
                self.webdriver.find_element(By.ID, "idSIButton9").click()
                break

            password_field.clear()
            time.sleep(3)
        time.sleep(3)

    def checkBingLogin(self):
        self.webdriver.get(
            "https://www.bing.com/fd/auth/signin?action=interactive&provider=windows_live_id&return_url=https%3A%2F%2Fwww.bing.com%2F"
        )
        while True:
            currentUrl = urllib.parse.urlparse(self.webdriver.current_url)
            if currentUrl.hostname == "www.bing.com" and currentUrl.path == "/":
                time.sleep(3)
                self.utils.tryDismissBingCookieBanner()
                with contextlib.suppress(Exception):
                    if self.utils.checkBingLogin():
                        return
            time.sleep(1)
