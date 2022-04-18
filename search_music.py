import argparse
import logging
from enum import Enum
from os import environ
from os.path import exists
from subprocess import getstatusoutput

import webdriver_manager.utils as utils
from requests.exceptions import ConnectionError
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.opera.options import Options as OperaOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.opera import OperaDriverManager

SAFARI_BROWSER_PATH = "/Applications/Safari.app"
SAFARI_DRIVER_PATH = "/usr/bin/safaridriver"
OPERA_BROWSER_PATH = "/Applications/Opera.app"

CHECK_INTERNET_CONNECTION_TIMEOUT = 3
WEB_DRIVER_WAIT_TIMEOUT = 3

BASE_URL = "https://yousician.com/songs"
SEARCH_INPUT_XPATH = "//input[@class='SearchInput__Input-sc-1o849ds-2 gmQnaU']"
SEARCH_PAGE_HEADER_XPATH = "//h4[@class='Typography__T-sc-174s9rz-0 ecaMCe']"
RESULTS_NOT_FOUND_XPATH = "//p[text()='There are no results.']"
SEARCH_RESULTS_XPATH = "//a/div/p"


class ConsoleColor:
    WHITE = '\u001b[37;1m'
    GREEN = '\u001b[32;1m'
    GREY = '\u001b[37m'
    YELLOW = '\u001b[33;1m'
    RED = '\u001b[31;1m'
    END_COLOR = '\033[0m'


class Browser(Enum):
    CHROME = "Chrome"
    CHROMIUM = "Chromium"
    FIREFOX = "Firefox"
    OPERA = "Opera"
    SAFARI = "Safari"

    def get_value(self):
        return self.value

    def __str__(self):
        return self.name

    def __eq__(self, y):
        return self.value == y.value

    def __hash__(self):
        return id(self)


def init():
    environ['WDM_LOG'] = '0'  # Turn off WebDriverManager logs
    environ['WDM_LOCAL'] = '1'  # Downloaded WebDriver will be placed in {project.dir}/.wdm instead of OS user folder
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, help="artist or song to search")
    return parser.parse_args()


def detect_browsers():
    logging.info(f"OS: {utils.os_type()}")
    browsers = collect_browsers()
    if browsers:
        logging.info(ConsoleColor.GREEN + "Found browsers:" + ConsoleColor.END_COLOR)
        index = 1
        for browser, version in browsers.items():
            logging.info(str(index) + ") " + browser.get_value() + " " + version)
            index += 1
        browsers_list = list(browsers.keys())
        index = input(
            ConsoleColor.WHITE + "Select browser by number or press \"Enter\" for using (1) browser: " + ConsoleColor.END_COLOR)
        if not index:
            return browsers_list[0]
        if not index.isdigit() or int(index) > len(browsers_list) or int(index) == 0:
            logging.error(ConsoleColor.RED + "Wrong browser number entered" + ConsoleColor.END_COLOR)
            exit(1)
        return browsers_list[int(index) - 1]
    else:
        logging.error(ConsoleColor.RED + "Installed browsers not found" + ConsoleColor.END_COLOR)
        exit(1)


def get_safari_version():
    return getstatusoutput(
        "/usr/libexec/PlistBuddy -c \"print :CFBundleShortVersionString\" /Applications/Safari.app/Contents/Info.plist")[1]


def find_opera_browser():
    if exists(OPERA_BROWSER_PATH):
        return {Browser.OPERA: getstatusoutput("/Applications/Opera.app/Contents/MacOS/Opera --version")[1]}


def collect_browsers():
    chrome = utils.get_browser_version_from_os(utils.ChromeType.GOOGLE)
    chromium = utils.get_browser_version_from_os(utils.ChromeType.CHROMIUM)
    firefox = utils.get_browser_version_from_os("firefox")
    opera = find_opera_browser()
    browsers = dict()
    if chrome:
        browsers.update({Browser.CHROME: chrome})
    if chromium:
        browsers.update({Browser.CHROMIUM: chromium})
    if firefox:
        browsers.update({Browser.FIREFOX: firefox})
    if opera:
        browsers.update(opera)
    if utils.os_type() == "mac64" and exists(SAFARI_BROWSER_PATH):
        browsers.update({Browser.SAFARI: get_safari_version()})
    return browsers


def ask_for_webdriver_path():
    webdriver_path = input(
        ConsoleColor.WHITE + "Provide path to WebDriver or press \"Enter\" and WebDriver will be downloaded: " + ConsoleColor.END_COLOR)
    if not webdriver_path:
        return webdriver_path
    if not exists(webdriver_path):
        logging.error(f"Webdriver in path {webdriver_path} doesn't exist")
        exit(1)
    return webdriver_path


def get_driver_options(browser):
    if browser == Browser.CHROME or browser == Browser.CHROMIUM:
        options = ChromeOptions()
        options.headless = True
        return options
    if browser == Browser.FIREFOX:
        options = FirefoxOptions()
        options.headless = True
        return options
    if browser == Browser.OPERA:
        options = OperaOptions()
        options.headless = True
        return options


def prepare_driver(browser):
    try:
        if browser == Browser.CHROME:
            return webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                                    options=get_driver_options(browser))
        elif browser == Browser.CHROMIUM:
            return webdriver.Chrome(
                service=Service(ChromeDriverManager(chrome_type=utils.ChromeType.CHROMIUM).install()),
                options=get_driver_options(browser))
        elif browser == Browser.FIREFOX:
            return webdriver.Firefox(service=Service(GeckoDriverManager().install()),
                                     options=get_driver_options(browser))
        elif browser == Browser.OPERA:
            return webdriver.Opera(executable_path=OperaDriverManager().install(), options=get_driver_options(browser))
        elif browser == Browser.SAFARI:
            return webdriver.Safari(service=Service(SAFARI_DRIVER_PATH))
    except ConnectionError:
        logging.error(ConsoleColor.RED + "No internet connection available." + ConsoleColor.END_COLOR)
        exit(1)


def check_input(search_input):
    if not search_input:
        search_input = input(ConsoleColor.YELLOW + "Song or artist for search: " + ConsoleColor.END_COLOR)
        if not search_input:
            logging.error(
                ConsoleColor.RED + "There is no input value neither argument is presented" + ConsoleColor.END_COLOR)
            exit(1)
    return search_input


def prepare_driver_with_path(browser, webdriver_path):
    if browser == Browser.CHROME:
        return webdriver.Chrome(service=Service(webdriver_path), options=get_driver_options(browser))
    elif browser == Browser.CHROMIUM:
        return webdriver.Chrome(service=Service(webdriver_path), options=get_driver_options(browser))
    elif browser == Browser.FIREFOX:
        return webdriver.Firefox(service=Service(webdriver_path), options=get_driver_options(browser))
    elif browser == Browser.OPERA:
        return webdriver.Opera(executable_path=webdriver_path, options=get_driver_options(browser))
    elif browser == Browser.SAFARI:
        return webdriver.Safari(service=Service(SAFARI_DRIVER_PATH))


def search_music(browser, webdriver_path, search_input):
    if webdriver_path:
        driver = prepare_driver_with_path(browser, webdriver_path)
    else:
        driver = prepare_driver(browser)
    logging.info(
        ConsoleColor.GREY + f"Searching for song / artist \"{search_input}\" with browser \"{browser.get_value()}\"" + ConsoleColor.END_COLOR)
    try:
        driver.get(BASE_URL)
    except WebDriverException:
        logging.error("No internet connection available.")
        exit(1)
    search_input_field = driver.find_element(by=By.XPATH, value=SEARCH_INPUT_XPATH)
    if browser == Browser.OPERA:
        search_input_field = driver.create_web_element(search_input_field["ELEMENT"])
    search_input_field.send_keys(search_input)
    search_input_field.submit()
    WebDriverWait(driver, WEB_DRIVER_WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, SEARCH_PAGE_HEADER_XPATH)))
    songs = driver.find_elements(by=By.XPATH, value=SEARCH_RESULTS_XPATH)
    if len(songs) == 0 and driver.find_element(By.XPATH, RESULTS_NOT_FOUND_XPATH).is_displayed():
        logging.info(ConsoleColor.RED + f"Songs for search input \"{search_input}\" not found" + ConsoleColor.END_COLOR)
        exit(1)
    texts = list()
    for song in songs:
        if browser == Browser.OPERA:
            song = driver.create_web_element(song["ELEMENT"])
        texts.append(song.text)
    songs_dictionary = dict(zip(texts[::2], texts[1::2]))
    sorted_by_artist = dict(sorted(songs_dictionary.items()))
    sorted_by_song = dict(sorted(sorted_by_artist.items(), key=lambda item: item[1]))
    logging.info(
        ConsoleColor.GREEN + f"{len(sorted_by_song.items())} results are found. Results:" + ConsoleColor.END_COLOR)
    for k, v in sorted_by_song.items():
        logging.info(v + " - " + k)
    driver.quit()


if __name__ == "__main__":
    init()
    args = parse_args()
    selected_browser = detect_browsers()
    webdriver_path_for_browser = ask_for_webdriver_path()
    search_input_from_user = check_input(args.input)
    search_music(selected_browser, webdriver_path_for_browser, search_input_from_user)
