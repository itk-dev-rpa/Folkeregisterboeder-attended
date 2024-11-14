"""This module handles interaction with eFlyt."""

import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from itk_dev_shared_components.eflyt import eflyt_search
from itk_dev_shared_components.misc import file_util


DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")


def login(username: str, password: str) -> webdriver.Chrome:
    """Opens a browser and logs in to Eflyt.

    Args:
        orchestrator_connection: The connection to Orchestrator.

    Returns:
        A selenium browser object.
    """
    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", {"download.default_directory": DOWNLOAD_DIR})
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    browser = webdriver.Chrome(options)
    browser.maximize_window()
    browser.get("https://notuskommunal.scandihealth.net/")

    user_field = browser.find_element(By.ID, "Login1_UserName")
    user_field.send_keys(username)

    pass_field = browser.find_element(By.ID, "Login1_Password")
    pass_field.send_keys(password)

    browser.find_element(By.ID, "Login1_LoginImageButton").click()

    return browser


def search_case_info(browser: webdriver.Chrome, case_number: str) -> tuple[str, str]:
    """Find the address of a given case in eFlyt and download the case journal.
    Try up to three times.

    Args:
        browser: The browser object already logged in to eFlyt.
        case_number: The case number of the case to find.

    Returns:
        The address of the given case and the file path of the downloaded journal.
    """
    for _ in range(3):
        try:
            eflyt_search.open_case(browser, case_number)

            address = browser.find_element(By.ID, "ctl00_ContentPlaceHolder2_ptFanePerson_stcPersonTab1_lblTiltxt").text
            address = address.replace("\n", ", ")

            journal_path = get_journal(browser)

            # Go back to main page
            browser.get("https://notuskommunal.scandihealth.net/web/SuperSearch.aspx")

            browser.minimize_window()

            return address, journal_path
        except Exception:
            pass

    return None, None


def get_journal(browser: webdriver.Chrome) -> str:
    """Download the case journal.

    Args:
        browser: The browser object already logged in to eFlyt and with the
        relevant case open.

    Raises:
        RuntimeError: If any unexpected files are downloaded.
        TimeoutError: If the file isn't downloaded within 10 seconds.

    Returns:
        The path to the downloaded file.
    """
    # Clear download dir
    for f in os.listdir(DOWNLOAD_DIR):
        os.remove(os.path.join(DOWNLOAD_DIR, f))

    browser.find_element(By.ID, "ctl00_ContentPlaceHolder2_ptFanePerson_stcPersonTab1_btnJournal").click()
    return file_util.wait_for_download(DOWNLOAD_DIR, file_name=None, file_extension=".pdf", timeout=20)
