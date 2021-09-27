from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import time
import logging
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
import pyperclip
from selenium.common.exceptions import NoSuchElementException, NoAlertPresentException, NoAlertPresentException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from DriverProvider import *

logger = logging.getLogger()
FORMAT = "[%(asctime)s][%(filename)s:%(lineno)3s - %(funcName)20s()] %(message)s"
logger.setLevel(logging.DEBUG)

LOGGED_IN = "LOGGED_IN"
LOGIN_SUCCESS = "LOGIN_SUCCESS"
LOGIN_FAIL = "LOGIN_FAIL"
LOGIN_ERROR = "LOGIN_ERROR"
LOGIN_VALIDATION = "LOGIN_VALIDATION"
LOGIN_IDENTIFICATION = "LOGIN_IDENTIFICATION"

def loginWithNaver(driver, id, pw, onlyAction=False):
    if not onlyAction:
        driver.get('https://band.us/home')

        if driver.current_url != 'https://band.us/home':
            return LOGGED_IN
    try:
        login_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="header"]/div/div/a[2]'))
        )
        login_btn.click()
        naver_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'uBtn.-icoType.-naver.externalLogin'))
        )
        naver_btn.click()

        """
        네이버 로그인
        """
        user_id = driver.find_element_by_id("id")
        password = driver.find_element_by_id("pw")
        time.sleep(1)

        user_id.click()
        pyperclip.copy(id)
        user_id.send_keys(Keys.CONTROL, 'v')
        time.sleep(1)

        password.click()
        pyperclip.copy(pw)
        password.send_keys(Keys.CONTROL, 'v')
        time.sleep(1)

        password.submit()
        
        time.sleep(3)

        if driver.current_url == 'https://band.us/':
            return LOGIN_SUCCESS
        return LOGIN_FAIL
    except:
        return LOGIN_ERROR

def loginWithPhone(driver, phone, pw, onlyAction=False):
    if not onlyAction:
        driver.get('https://auth.band.us/phone_login?keep_login=true')
        
        if driver.current_url != 'https://auth.band.us/phone_login?keep_login=true':
            return LOGGED_IN
    try:
        """
        휴대폰으로 로그인
        """
        input_phone = driver.find_element_by_id("input_local_phone_number")
        input_phone.click()
        pyperclip.copy(phone)
        input_phone.clear()
        input_phone.send_keys(Keys.CONTROL, 'v')
        submit_btn = driver.find_element_by_xpath('//*[@id="phone_login_form"]/button')
        submit_btn.click()
        time.sleep(1)

        password = driver.find_element_by_id("pw")
        password.click()
        pyperclip.copy(pw)
        password.clear()
        password.send_keys(Keys.CONTROL, 'v')
        password.submit()
        time.sleep(1)
        
        time.sleep(3)

        if driver.current_url == 'https://band.us/':
            return LOGIN_SUCCESS
        elif driver.current_url == 'https://auth.band.us/b/validation/phone_number?next_url=https%3A%2F%2Fband.us':
            return LOGIN_VALIDATION
        return LOGIN_FAIL
    except Exception as e:
        logging.exception("")
        return LOGIN_ERROR

def loginWithEmail(driver, email, pw, onlyAction=False):
    if not onlyAction:
        driver.get('https://auth.band.us/email_login?keep_login=true')
        
        if driver.current_url != 'https://auth.band.us/email_login?keep_login=true':
            return LOGGED_IN
    try:
        """
        이메일 로그인
        """
        input_email = driver.find_element_by_id("input_email")
        input_email.click()
        pyperclip.copy(email)
        input_email.clear()
        input_email.send_keys(Keys.CONTROL, 'v')
        input_email.send_keys(Keys.ENTER)
        
        time.sleep(1)

        password = driver.find_element_by_id("pw")
        password.click()
        pyperclip.copy(pw)
        password.clear()
        password.send_keys(Keys.CONTROL, 'v')
        password.submit()
        time.sleep(1)
        
        time.sleep(3)

        if driver.current_url == 'https://band.us/':
            return LOGIN_SUCCESS
        elif driver.current_url == 'https://auth.band.us/b/validation/phone_number?next_url=https%3A%2F%2Fband.us':
            trust = driver.find_element_by_id("trust")
            trust.click()
            return LOGIN_VALIDATION
        elif driver.current_url == 'https://auth.band.us/show_user_account_status':
            return LOGIN_IDENTIFICATION
        return LOGIN_FAIL
    except Exception:
        logging.exception("")
        return LOGIN_ERROR

class ValidateAccountThread(QThread):
    state_logged_in = pyqtSignal()
    state_login_success = pyqtSignal()
    state_login_fail = pyqtSignal()
    state_login_error = pyqtSignal()
    state_login_validation = pyqtSignal()
    state_login_identification = pyqtSignal()

    path = ''
    id = ''
    pw = ''
    ip = ''

    def __init__(self, parent=None):
        super().__init__()
        parent.state_validation_finished.connect(self.state_validation_finished)
        parent.state_identification_finished.connect(self.state_identification_finished)

    def run(self):
        try:
            self.driver = setup_driver(self.ip)
            result = loginWithEmail(self.driver, self.id, self.pw, onlyAction=False)
            if result == LOGIN_VALIDATION:
                self.state_login_validation.emit()
            elif result == LOGIN_IDENTIFICATION:
                self.state_login_identification.emit()
            else:
                signal = {
                    LOGGED_IN:self.state_logged_in,
                    LOGIN_SUCCESS:self.state_login_success,
                    LOGIN_FAIL:self.state_login_fail,
                    LOGIN_ERROR:self.state_login_error
                }.get(result)
                signal.emit()
                
                self.driver.close()
                self.driver.quit()
        except:
            logging.exception("")

    def state_validation_finished(self):
        logging.debug(self.driver.current_url)

        if self.driver.current_url == 'https://band.us/':
            self.state_login_success.emit()
        else:
            self.state_login_error.emit()
        
        self.driver.close()
        self.driver.quit()

    def state_identification_finished(self):
        if self.driver.current_url == 'https://band.us/':
            self.state_login_success.emit()
        else:
            self.state_login_error.emit()
        
        self.driver.close()
        self.driver.quit()

    def stop(self):
        try:
            self.isRunning = False
            self.quit()
            self.driver.close()
            self.driver.quit()
            self.on_logging_send_msg.emit(self.LOGGING_INFO, "작업이 취소됨")
        except Exception as e:
            self.on_logging_send_msg.emit(self.LOGGING_WARNING, "제거할 드라이버 없음 : "+str(e))