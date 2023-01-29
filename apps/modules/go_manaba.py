from contextlib import suppress

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from settings import MANABA_HOME_URL


def go_manaba(driver: WebDriver):
    """manabaのホームページに移動する

    Args:
        driver (WebDriver): ブラウザを操作するドライバー（Selenium）
    """

    # manabaのホームに移動する（ユーザーデータを用いた自動ログインが行われる）
    driver.get(MANABA_HOME_URL)
    WebDriverWait(driver, 30).until(
        EC.visibility_of_all_elements_located)  # ページが読み込まれるまで待機（最大30秒）

    # manabaのページに移動できたかを確認（ワンタイムパスワード打ち込み画面の可能性がある）
    current_url = driver.current_url
    if current_url != MANABA_HOME_URL:
        print("Failed to move manaba. Current URL:", current_url)

    # manabaの時間割をリスト形式にする
    css_selector = "#container > div.pagebody > div > div.contentbody-left > div.my-infolist.my-infolist-mycourses.my-infolist-mycourses-weekly > ul > li:nth-child(2) > a"
    with suppress(NoSuchElementException):
        driver.find_element(By.CSS_SELECTOR, css_selector).click()
        # すでにリスト形式になっている場合は何もせずに次に進む
