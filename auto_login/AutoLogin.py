from dotenv import load_dotenv
import json
import os
import random
import string
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from time import sleep
from undetected_chromedriver import Chrome, ChromeOptions
import warnings

class GoogleBardAutoLogin():
    def __init__(self, google_account, google_password, chrome_version):
        print('Inicjowanie automatycznego logowania dla Google Bard ...')
        self.google_account = google_account
        self.google_password = google_password
        self.chrome_version = chrome_version
        warnings.simplefilter('ignore', DeprecationWarning)
        warnings.simplefilter('ignore', ResourceWarning)
        options = ChromeOptions()
        options.add_argument('--headless') # comment this if you want to see the chrome window
        self.driver = Chrome(version_main=self.chrome_version, options=options)

        google_bard_url = 'https://bard.google.com/'
        print(f'Zwiedzanie {google_bard_url} ...')
        self.driver.get(google_bard_url)
        self.driver.maximize_window()

    def find_sign_in_button(self):
        print('Znajdowanie przycisku logowania ...')
        spans = self.driver.find_elements(By.TAG_NAME, 'span')
        for span in spans:
            if span.text.strip() == 'Sign in':
                return span
        raise NoSuchElementException('Żaden element nie ma wewnętrznej wartości tekstowej - "Sign in"')

    def find_account_input(self):
        self.find_sign_in_button().click()
        print('Kliknięcie przycisku logowania ...')
        print('Znajdowanie danych wejściowych konta ...')
        return self.driver.find_element(By.NAME, 'identifier')

    def find_password_input(self):
        try:
            self.find_account_input().send_keys(self.google_account + Keys.RETURN)
            print('Wprowadzanie konta ...')
            WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.NAME, 'Passwd')))
            print('Znajdowanie wprowadzonego hasła ...')
            return self.driver.find_element(By.NAME, 'Passwd')
        except TimeoutException:
            print('Limit czasu logowania dla połączenia sieciowego. Spróbuj ponownie.')
            return None

    def get_cookie_list(self):
        try:
            password_input = self.find_password_input()
            if password_input != None:
                print('Wprowadzanie hasła ...')
                password_input.send_keys(self.google_password + Keys.RETURN)
                WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.CLASS_NAME, 'mdc-button__label')))
                print('Znajdowanie plików cookie aplikacji ...')
                return self.driver.get_cookies()
            else:
                return None
        except TimeoutException:
            print('Limit czasu logowania dla połączenia sieciowego. Spróbuj ponownie.')
            return None

    def get_cookie(self):
        cookie_list = self.get_cookie_list()
        if cookie_list != None:
            print('Znajdowanie cookie "__Secure-1PSID" ...')
            for cookie_dict in cookie_list:
                if cookie_dict['name'] == '__Secure-1PSID':
                    return cookie_dict['value']
            raise NoSuchElementException('Żaden element nie ma wartości "__Secure-1PSID" w kluczu "name".')
        else:
            return None

class MicrosoftBingAutoLogin():
    def __init__(self, bing_account, bing_password, chrome_version):
        print('Inicjowanie automatycznego logowania dla Microsoft Bing ...')
        self.bing_account = bing_account
        self.bing_password = bing_password
        self.chrome_version = chrome_version
        warnings.simplefilter('ignore', DeprecationWarning)
        warnings.simplefilter('ignore', ResourceWarning)
        options = ChromeOptions()
        options.add_argument('--headless') # comment this if you want to see the chrome window
        self.driver = Chrome(version_main=self.chrome_version, options=options)

        print('Generowanie losowych sig i CSRFToken dla żądanego adresu url ...')
        sig = ''.join([random.choice(string.ascii_letters + string.digits).upper() for _ in range(32)])
        CSRFToken = ''.join([random.choice(string.ascii_letters + string.digits).upper() for _ in range(8)]
        + [random.choice(string.ascii_letters + string.digits).upper() for _ in range(4)]
        + [random.choice(string.ascii_letters + string.digits).upper() for _ in range(4)]
        + [random.choice(string.ascii_letters + string.digits).upper() for _ in range(4)]
        + [random.choice(string.ascii_letters + string.digits).upper() for _ in range(12)])

        print('Odwiedzenie strony logowania Microsoft Bing ...')
        self.driver.get(f'https://login.live.com/login.srf?wa=wsignin1.0&rpsnv=13&id=264960&wreply=https%3a%2f%2fwww.bing.com%2fsecure%2fPassport.aspx%3fedge_suppress_profile_switch%3d1%26requrl%3dhttps%253a%252f%252fwww.bing.com%252fsearch%253ftoWww%253d1%2526redig%253d9220EACAFFCA40508E4E7BD52023921B%2526q%253dBing%252bAI%2526showconv%253d1%2526wlexpsignin%253d1%26sig%3d{sig}&wp=MBI_SSL&lc=1028&CSRFToken={CSRFToken}&aadredir=1')
        self.driver.maximize_window()

    def find_account_input(self):
        print('Znajdowanie danych wejściowych konta ...')
        return self.driver.find_element(By.NAME, 'loginfmt')

    def find_password_input(self):
        self.find_account_input().send_keys(self.bing_account + Keys.RETURN)
        print('Wprowadzanie konta ...')
        WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.NAME, 'passwd')))
        print('Znajdowanie wprowadzonego hasła ...')
        return self.driver.find_element(By.NAME, 'passwd')

    def get_cookies(self):
        self.find_password_input().send_keys(self.bing_password + Keys.RETURN)
        print('Wprowadzanie hasła ...')
        bing_chat_url = 'https://bing.com/chat'
        print(f'Zwiedzanie {bing_chat_url} ...')
        self.driver.get(bing_chat_url)
        sleep(2)
        print('Znajdowanie plików cookie aplikacji ...')
        return self.driver.get_cookies()

    def dump_cookies(self):
        cookies = self.get_cookies()
        json_file = 'cookies.json'
        print(f'Dump {json_file} ...')
        with open(json_file, 'w') as f:
            json.dump(cookies, f, indent=2)