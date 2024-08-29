import argparse
import contextlib
import logging
import time
from argparse import Namespace
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from undetected_chromedriver import Chrome
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException
from src.browser import Browser

class Login:
    browser: Browser
    args: Namespace
    webdriver: Chrome

    def __init__(self, browser: Browser, args: argparse.Namespace):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.utils = browser.utils
        self.args = args

    def click_element_if_visible(self, element):
        try:
            if element.is_displayed() and element.is_enabled():
                element.click()
                logging.critical(f"This Account is Locked!")
                self.webdriver.close()
                self.webdriver.quit()
            else:
                pass
        except (ElementNotInteractableException, NoSuchElementException):
            pass
    def checklockedUser(self):
        try:
            element = self.webdriver.find_element(By.XPATH, "//div[@id=\'serviceAbuseLandingTitle\']")
            self.click_element_if_visible(element)
        except NoSuchElementException:
            pass

    def login(self) -> None:
        if self.utils.isLoggedIn():
            logging.info("[LOGIN] Already logged-in")
        else:
            logging.info("[LOGIN] Logging-in...")
            self.executeLogin()
            logging.info("[LOGIN] Logged-in successfully !")
        assert self.utils.isLoggedIn()


    def executeLogin(self) -> None:
        self.utils.waitUntilVisible(By.ID, "i0116")
        emailField = self.utils.waitUntilClickable(By.NAME, "loginfmt")
        logging.info("[LOGIN] Entering email...")
        emailField.click()
        emailField.send_keys(self.browser.username)
        assert emailField.get_attribute("value") == self.browser.username
        self.utils.waitUntilClickable(By.ID, "idSIButton9").click()
        isTwoFactorEnabled: bool = False
        with contextlib.suppress(TimeoutException):
            self.utils.waitUntilVisible(By.ID, "pushNotificationsTitle")
            isTwoFactorEnabled = True
        logging.debug(f"isTwoFactorEnabled = {isTwoFactorEnabled}")




        if isTwoFactorEnabled:
            assert (self.args.visible), "2FA detected, run in visible mode to handle login"
            print("2FA detected, handle prompts and press enter when on keep me signed in page")
            input()

            with contextlib.suppress(TimeoutException):
                self.utils.waitUntilVisible(By.NAME, "kmsiForm")
                self.utils.waitUntilClickable(By.ID, "acceptButton").click()
        else:
            passwordField = self.utils.waitUntilClickable(By.NAME, "passwd")
            logging.info("[LOGIN] Entering password...")
            passwordField.click()
            passwordField.send_keys(self.browser.password)
            assert passwordField.get_attribute("value") == self.browser.password
            self.utils.waitUntilClickable(By.ID, "idSIButton9").click()
            time.sleep(1)
            self.checklockedUser()
            time.sleep(2)
            self.utils.waitUntilVisible(By.NAME, "kmsiForm")
            self.utils.waitUntilClickable(By.ID, "acceptButton").click()


        isAskingToProtect = self.utils.checkIfTextPresentAfterDelay("protect your account")
        logging.debug(f"isAskingToProtect = {isAskingToProtect}")

        if isAskingToProtect:
            assert (self.args.visible), "Account protection detected, run in visible mode to handle login"
            print("Account protection detected, handle prompts and press enter when on rewards page")
            input()

        self.utils.waitUntilVisible(By.CSS_SELECTOR, 'html[data-role-name="RewardsPortal"]')
