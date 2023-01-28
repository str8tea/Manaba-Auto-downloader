from __future__ import annotations
from dataclasses import dataclass
from time import sleep

from bs4 import BeautifulSoup
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .course_list import CourseList
from .file_history import FileHistory
from .file_metadata import FileMetadata
from settings import FILE_HISTORY_JSON_PATH


@dataclass(frozen=True, slots=True)
class DownloadContent:
    """ダウンロードするコンテンツの名前（講義の名前も含む）を表すデータクラス

    メンバ変数の講義のコンテンツからダウンロードを行う
    """

    course_name: str
    content_name: str

    def _download_attachments(self, driver: WebDriver, link: str):
        """引数のリンクにアクセスし、そのページにある添付ファイルをダウンロードする

        Args:
            driver (Webdriver): ブラウザを操作するドライバー（Selenium）
            link (str): 添付ファイルがあるリンク
        """

        driver.get(link)
        WebDriverWait(driver, 30).until(
            EC.visibility_of_all_elements_located)  # ページが読み込まれるまで待機（最大30秒）
        sleep(1)

        html = driver.page_source.encode("utf-8")  # 今開いているhtmlを取得

        soup = BeautifulSoup(html, "html.parser")  # htmlを「html.parser」で解析する
        # course_name = soup.find("a", id="coursename")["title"].strip() # 講義名
        body = soup.find("div", class_="contentbody-left")  # コンテンツの中身
        page_title = body.find("h1", class_="pagetitle").get_text(
            strip=True)  # ページタイトル
        attachment_files = body.find_all(
            "div", class_="inlineattachment")  # 添付ファイルのソースが入るリスト

        # 添付ファイルが無い場合
        if attachment_files == []:
            print(
                f"Attachment was not found in {page_title} of {self.course_name}")
            return

        # ダウンロードしたファイルの履歴をJSONファイルから生成する
        file_history = FileHistory.from_json(FILE_HISTORY_JSON_PATH)

        # 添付ファイルをダウンロードしてファイルの履歴にそのファイルのメタデータを代入する
        for f in attachment_files:
            file_metadata = FileMetadata.from_soup(
                f, self.course_name, self.content_name, page_title)
            file_metadata.download_by(driver)
            file_history.add(file_metadata)

        # ダウンロードしたファイルが加わった履歴をJSONファイルに書き込む
        file_history.to_json(FILE_HISTORY_JSON_PATH)

    def download_content(self, driver: WebDriver, course_list: CourseList) -> None:
        """コンテンツ内の未読のページにある添付ファイルをダウンロードする

        引数の講義の一覧から、目的のコンテンツのリンクを探す。
        見つかったらそのリンクに移動し、コンテンツ内の未読のページを探す。
        見つかったらそのページにある未読の添付ファイルをダウンロードする

        Args:
            driver (Webdriver): ブラウザを操作するドライバー（Selenium）
            course_list (CourseList): 講義の一覧
        """

        # ダウンロードするコンテンツをコースリストから探す
        course = course_list.search_course(self.course_name)
        if course is None:
            return

        content = course.search_content(self.content_name)
        if content is None:
            return

        # 目的のコンテンツのリンクに移動
        driver.get(content.link)
        WebDriverWait(driver, 30).until(
            EC.visibility_of_all_elements_located)  # ページが読み込まれるまで待機（最大30秒）
        sleep(1)

        # 未読のページを探す
        unread_css_selector = \
            "#container > div.pagebody > div.contents > div > div > div.articlebody > div.contentbody-right > div > table > tbody > tr:nth-child(2) > td > ul > li.GRIread"
        unread_items = driver.find_elements(
            by=By.CSS_SELECTOR, value=unread_css_selector)
        if unread_items == []:
            print(f"No unread contents in {content.name} of {course.name}")
            return

        # 未読の各ページに移動し、添付ファイルをダウンロードする
        unread_links = [item.find_element_by_tag_name(
            "a").get_attribute("href") for item in unread_items]
        for link in unread_links:
            self._download_attachments(driver, link)  # 添付ファイルをダウンロードする
