from __future__ import annotations
from dataclasses import dataclass, field
import re
from time import sleep

from bs4 import BeautifulSoup
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .content import Content
from settings import MANABA_CLIENT_URL


@dataclass(slots=True)
class Course:
    """講義を表すデータクラス

    講義内のコンテンツの取得やコンテンツの検索を行う

    Note:
        from_soupから生成されることを想定
    """

    name: str
    link: str
    year: int  # ex) 2000
    semester: str  # 前期、後期、通年、Unknownのいずれかが入る
    day: str  # ex) 月曜（不明の場合はUnknown）
    period: str  # ex) 1限（不明の場合はUnknown）
    professor: str
    content_list: list[Content] = field(
        default_factory=list)  # この講義内のコンテンツのリスト

    # スケジュールの各項目の正規表現
    semester_regex = re.compile(r'(前期|後期|通年)')
    day_regex = re.compile(r'[日月火水木金土]曜')
    period_regex = re.compile(r'[1-5]限')

    def __post_init__(self):
        self.name.removesuffix(" ")  # 末尾の空白文字を削除（ディレクトリ名に使われるため）

        # content_listの各要素が辞書型の場合は、Content型のデータクラスに変換する（CourseList.from_json()で辞書型をデータクラスに変換する際に呼ばれる）
        self.content_list = [Content(**content)
                             for content in self.content_list if isinstance(content, dict)]

    @classmethod
    def from_soup(cls, course_table_raw_soup: BeautifulSoup) -> Course:
        """引数の講義の一覧表の1行分のソースから自身のインスタンスを生成する

        Args:
            course_table_raw_soup (BeautifulSoup): manabaのホームページにある講義の一覧表の1行分のソース（BeautifulSoupで解析済みのもの）

        Returns:
            Course: 講義の各情報（content_listは除く）を引数とした自身のインスタンス
        """

        course_info = course_table_raw_soup.find_all("td")
        header = course_info[0].find("span", class_="courselist-title")
        name = header.get_text(strip=True)
        link = header.find("a")["href"]
        full_link = MANABA_CLIENT_URL + link
        year = course_info[1].get_text()
        professor = course_info[3].get_text()  # 教授名

        # スケジュールを取り出す（不明の場合はUnkown）
        # 〇〇  〇〇  〇〇の形式（左から学期、曜日、時限）※空白文字はnbsp
        schedule = course_info[2].get_text(strip=True)

        # 学期
        if m := re.search(Course.semester_regex, schedule):
            semester = m.group()
        else:
            semester = "Unknown"
        # 曜日
        if m := re.search(Course.day_regex, schedule):
            day = m.group()
        else:
            day = "Unknown"
        # 時限
        if m := re.search(Course.period_regex, schedule):
            period = m.group()
        else:
            period = "Unknown"

        # 得られた講義の各情報からコースクラスのインスタンスを生成
        return cls(name, full_link, year, semester, day, period, professor)

    def fetch_content_list(self, driver: WebDriver) -> None:
        """この講義がもつコンテンツの一覧を講義ページから取得して、メンバ変数content_listに格納する

        Args:
            driver (WebDriver): ブラウザを操作するドライバー（Selenium）
        """

        # 講義ページに移動
        driver.get(self.link)
        WebDriverWait(driver, 10).until(EC.visibility_of_all_elements_located)
        sleep(1)

        # 講義ページから各コンテンツのソースを取得
        html = driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, "html.parser")  # htmlを「html.parser」で解析する
        content_list_body = soup.find(
            "div", class_="top-contents-list-body")  # 全てのコンテンツ（カード型レイアウト）のソース
        content_card_list = content_list_body.find_all(
            "div", class_="contents-card")  # 各コンテンツのソースが入るリスト

        # 各ソースから、Contentインスタンスのリストを作成する
        content_list = [Content.from_soup(content_card)
                        for content_card in content_card_list]

        # コンテンツの一覧を格納する
        self.content_list = content_list

    def search_content(self, name: str) -> Content:
        """メンバ変数のコンテンツの一覧から、引数の名前を含むコンテンツを検索する

        Args:
            name (str): 検索するコンテンツ名

        Returns:
            Content: 目的のコンテンツ（見つからなかった場合や複数ある場合はNone）

        Note:
            引数の名前を含むコンテンツが複数ある場合はNoneを返す
            ただし、引数の名前のコンテンツがある場合は、そのコンテンツを返す
            ex) コンテンツの一覧に'講義資料'と'講義資料前準備'の2つがある場合、'講義資料'で検索したら、'講義資料'のコンテンツを返す
        """

        # 完全一致検索を行う（結果はリスト）
        exact_match_result = list(
            filter(lambda content: name == content.name, self.content_list))
        if len(exact_match_result) == 1:
            return exact_match_result[0]

        # 部分一致検索を行う（結果はリスト）
        partial_match_result = list(
            filter(lambda content: name in content.name, self.content_list))
        match len(partial_match_result):
            case 0:
                print(f"'{name}' is not found")
                return None
            case 1:
                return partial_match_result[0]
            case _:
                print(
                    f"Contents names including '{name}' are more than one. Please search by more words again.")
                return None
