# manabaから講義資料を自動でダウンロードするプログラム

from __future__ import annotations
from dataclasses import dataclass, field, asdict
import json
import os
import re
from shutil import move
from time import sleep
import traceback

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from go_manaba import go_manaba
from launch_browser import launch_browser
from settings import MANABA_URL, USERDATA_DIR, SAVE_DIR, FILE_HISTORY_JSON_PATH, COURSE_LIST_JSON_PATH, DOWNLOAD_CONTENT_NAME_LIST_JSON_PATH, IS_UPDATE_COURSE_LIST


@dataclass(frozen=True, slots=True)
class Content:
    """各講義のコンテンツを表すデータクラス

    Note: 
        self.from_soupから生成されることを想定
    """

    name: str
    link: str
    update_date: str  # ex) 2000-01-01 00:00

    @classmethod
    def from_soup(cls, content_card_soup: BeautifulSoup) -> Content:
        """コンテンツのソースから自身のインスタンスを生成する

        Args:
            content_card_soup (BeautifulSoup): カード型レイアウトのコンテンツのソース（BeautifulSoupで解析済みのもの）

        Returns:
            Content: 生成した自身のインスタンス
        """

        # 引数のソースから、コンテンツの各情報を取得
        header = content_card_soup.find("div", class_="contents-card-title")
        name = header.find("a").get_text(strip=True)
        link = header.find("a")["href"]
        full_link = MANABA_URL + link
        update_date = header.find("span").get_text()

        return cls(name, full_link, update_date)


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
            course_table_raw_soup (BeautifulSoup): manabaのホームページにある講義の一覧表の1行分のソース

        Returns:
            Course: 講義の各情報（content_listは除く）を引数とした自身のインスタンス
        """

        course_info = course_table_raw_soup.find_all("td")
        header = course_info[0].find("span", class_="courselist-title")
        name = header.get_text(strip=True)
        link = header.find("a")["href"]
        full_link = MANABA_URL + link
        year = course_info[1].get_text()
        professor = course_info[3].get_text()  # 教授名

        # スケジュールを取り出す（不明の場合はUnkown）
        # 〇〇  〇〇  〇〇の形式（左から学期、曜日、時限）※空白文字はnbsp
        schedule = course_info[2].get_text(strip=True)

        # 学期
        m = re.search(Course.semester_regex, schedule)
        if m:
            semester = m.group()
        else:
            semester = "Unknown"
        # 曜日
        m = re.search(Course.day_regex, schedule)
        if m:
            day = m.group()
        else:
            day = "Unknown"
        # 時限
        m = re.search(Course.period_regex, schedule)
        if m:
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

        Note:
            引数の名前を含むコンテンツが複数ある場合はNoneとする
            ただし、引数の名前のコンテンツがある場合は、そのコンテンツを返す
            ex) コンテンツの一覧に'講義資料'と'講義資料前準備'の2つがある場合、'講義資料'で検索したら、'講義資料'のコンテンツを返す

        Returns:
            Content: 目的のコンテンツ（見つからなかった場合や複数ある場合はNone）
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


class CourseList:
    """コースの一覧を表すクラス

    コースの一覧のJSONの入出力処理、コースの検索を行う

    Attributes:
        course_list (list[Course]): 

    Note:
        manabaのホームページまたはJSONファイルから生成することを想定
    """

    __slots__ = ("course_list")

    def __init__(self, course_list):
        self.course_list = course_list

    @classmethod
    def from_manaba(cls, driver: WebDriver) -> CourseList:
        """manabaのホームページに行き、そのソースから自身のインスタンスを生成する

        Args:
            driver (Webdriver): 

        Returns:
            CourseList: 講義の一覧を引数とした自身のインスタンス
        """

        go_manaba(driver)

        # htmlを解析して講義の一覧表を得る
        html = driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, "html.parser")
        course_list_soup = soup.find(
            "table", class_="stdlist courselist")  # 講義の一覧表
        if course_list_soup is None:
            print(f"No courses in {html}")
            return cls([])
        course_raws_soup = course_list_soup.find_all("tr")
        del course_raws_soup[0]  # 表のヘッダー部分である先頭要素を削除

        # 講義の一覧表のsoupから講義の一覧を生成する
        course_list = []
        for course_raw_soup in course_raws_soup:
            course = Course.from_soup(course_raw_soup)
            course.fetch_content_list(driver)
            course_list.append(course)

        return cls(course_list)

    @classmethod
    def from_json(cls, json_filename: str) -> CourseList:
        """JSONファイルから自身のインスタンスを生成する

        Args:
            json_filename (str): 講義の一覧が記載されたJSONファイルの名前

        Returns:
            CourseList: 講義の一覧を引数とした自身のインスタンス
        """

        with open(json_filename, "r", encoding='utf-8') as f:
            course_dict_list = json.load(f)  # JSONデータを辞書形式で読み取る

        # 辞書型のコースが入るリストをCourse型のコースが入るリストに変換する
        course_list = [Course(**course_dict)
                       for course_dict in course_dict_list]

        return cls(course_list)

    def to_json(self, json_filename: str) -> None:
        """講義の一覧をJSONファイルに書き込み

        Args:
            json_filename (str): 書き込み先のJSONファイルの名前（上書きされる）
        """

        if self.course_list == []:
            print("Course list is empty")
            return

        # Course型のコースが入るリストを辞書型のコースが入るリストに変換する
        course_dict_list = [asdict(course) for course in self.course_list]

        with open(json_filename, "w", encoding="utf-8") as f:
            # JSON形式でファイルに書き込む
            json.dump(course_dict_list, f, ensure_ascii=False)

    def search_course(self, name: str) -> Course:
        """メンバ変数の講義の一覧から、引数の名前を含む講義を検索する（Course.search_contentとアルゴリズムは同じ）

        Args:
            name (str): 検索する講義名

        Note:
            引数の名前を含む講義が複数ある場合はNoneとする
            ただし、引数の名前の講義がある場合は、その講義を返す
            ex) 講義の一覧に'情報工学'と'情報工学実験'の2つがある場合、'情報工学'で検索したら、'情報工学'の講義を返す

        Returns:
            Content: 目的の講義（見つからなかった場合や複数ある場合はNone）
        """

        # 完全一致検索を行う（結果はリスト）
        exact_match_result = list(
            filter(lambda course: name == course.name, self.course_list))
        if len(exact_match_result) == 1:
            return exact_match_result[0]

        # 部分一致検索を行う（結果はリスト）
        partial_match_result = list(
            filter(lambda course: name in course.name, self.course_list))
        match len(partial_match_result):
            case 0:
                print(f"'{name}' is not found")
                return None
            case 1:
                return partial_match_result[0]
            case _:
                print(
                    f"Course names including '{name}' are more than one. Please search by more words again.")
                return None


@dataclass(slots=True)
class FileMetadata:
    name: str
    link: str
    upload_date: str  # フォーマットは2000-01-01 00:00:00
    course_name: str
    content_name: str
    page_title: str
    description: str
    path: str = "Not downloaded"
    can_download: bool = False

    @classmethod
    def from_soup(cls, file_soup: BeautifulSoup, course_name: str = "Unknown", content_name: str = "Unknown", page_title: str = "Unknown") -> FileMetadata:
        detail = file_soup.find("div", class_="inlineaf-description").find("a")
        file_link = detail["href"]
        file_full_link = MANABA_URL + file_link
        detail_text = detail.get_text(strip=True)

        # ファイルの説明がある（2行ある）場合は、1行目が説明、2行目がファイルのヘッダー
        if "<br>" in detail_text:
            description, file_header = detail_text.split("<br>")
        else:
            description = "Nothing"
            file_header = detail_text

        # headerの形式は「ファイル名 - アップロード日時」なので正規表現で取り出す
        header_regex = re.compile(
            r'(.+\.[a-z]+) - (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
        m = re.match(header_regex, file_header)
        if m:
            file_name, file_upload_date = m.groups()
        else:
            file_name = "Unknown"
            file_upload_date = "Unknown"

        return cls(file_name, file_full_link, file_upload_date, course_name, content_name, page_title, description)

    def download_by(self, driver: WebDriver) -> None:

        # ファイルをダウンロードする
        driver.get(self.link)
        file_path = os.path.join(SAVE_DIR, self.name)

        # 講義名のディレクトリを作成する
        course_dir = os.path.join(SAVE_DIR, self.course_name)
        os.makedirs(course_dir, exist_ok=True)  # ディレクトリが既にある場合は何もしない

        # ダウンロードしたファイルの移動先の設定
        dest_path = os.path.join(course_dir, self.name)

        # ダウンロードしたファイルを講義名のディレクトリに移動させる
        for _ in range(10):
            # ダウンロードが完了していない可能性があるので、2秒間隔で10回ダウンロードしたファイルの移動を試みる
            sleep(2)
            # ダウンロードに成功した場合
            if os.path.isfile(file_path):
                try:
                    print(
                        f"succeeded to download '{self.name}' in {self.page_title} of {self.course_name}")
                    self.can_download = True
                    move(file_path, dest_path)  # dest_pathへファイルを移動する
                except:
                    print(
                        f"failed to move '{self.name}' in {self.page_title} of {self.course_name}")
                    print(traceback.format_exc())
                    dest_path = file_path
                else:
                    print(
                        f"succeeded to move '{self.name}' in {self.page_title} of {self.course_name}")
                finally:
                    break
        # ダウンロードしたはずのファイルが見つからなかった場合
        else:
            print(
                f"failed to download '{self.name}' in {self.page_title} of {self.course_name}")
            dest_path = "Unknown"

        self.path = dest_path  # パスを更新する

    def to_json(self, json_filename: str) -> None:

        # 辞書型に変換する
        file_dict = asdict(self)

        with open(json_filename, "a", encoding="utf-8") as f:
            # JSON形式でファイルに追記する
            json.dump(file_dict, f, ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class FileHistory:
    file_history: list[FileMetadata]

    @classmethod
    def from_json(cls, json_filename: str) -> FileHistory:

        # JSONファイルがない場合は新規作成する
        if not os.path.isfile(json_filename):
            with open(json_filename, "w") as f:
                pass
            return cls([])

        # JSONファイルの中身が空の場合
        if os.path.getsize(json_filename) == 0:
            return cls([])

        # JSONファイルからダウンロードしたファイルの履歴を辞書形式で読み取る
        with open(json_filename, "r", encoding='utf-8') as f:
            file_metadata_dict_list = json.load(f)

        # 辞書型のファイルが入るリストをFileMetadata型のファイルが入るリストに変換する
        file_history = [FileMetadata(**file_dict)
                        for file_dict in file_metadata_dict_list]

        return cls(file_history)

    def add(self, file_metadata: FileMetadata):
        self.file_history.append(file_metadata)

    def to_json(self, json_filename: str) -> None:

        # FileMetadata型のファイルが入るリストを辞書型のファイルが入るリストに変換する
        file_metadata_dict_list = [
            asdict(file_metadata) for file_metadata in self.file_history]

        with open(json_filename, "w", encoding="utf-8") as f:
            # JSON形式でファイルに書き込む
            json.dump(file_metadata_dict_list, f, ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class DownloadContentName:
    course_name: str
    content_name: str

    def download_attachments(self, driver, link: str):

        # コンテンツがあるリンクに移動
        driver.get(link)
        WebDriverWait(driver, 30).until(
            EC.visibility_of_all_elements_located)  # ページが読み込まれるまで待機（最大30秒）
        sleep(1)

        html = driver.page_source.encode('utf-8')  # htmlを取得
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

    def download_content(self, driver, course_list: CourseList):

        # ダウンロードするコンテンツをコースリストから探す
        course = course_list.search_course(self.course_name)
        if course is None:
            print(f"Failed to download from {course.name}")
            return

        content = course.search_content(self.content_name)
        if content is None:
            print(f"Failed to download from {content.name}")
            return

        self.download_attachments(driver, content.link)


@dataclass(frozen=True, slots=True)
class DownloadContentNameList:
    content_name_list: list[DownloadContentName]

    @classmethod
    def from_json(cls, json_filename: str) -> DownloadContentNameList:
        with open(json_filename, "r", encoding='utf-8') as f:
            content_name_dict_list = json.load(f)  # JSONデータを辞書形式で読み取る

        # 辞書型のダウンロードするコンテンツの名前が入るリストをDownloadContentName型の名前が入るリストに変換する
        content_name_list = [DownloadContentName(
            **content_name_dict) for content_name_dict in content_name_dict_list]

        return cls(content_name_list)

    def download_contents(self, driver, course_list: CourseList):
        for content_name in self.content_name_list:
            content_name.download_content(driver, course_list)


if __name__ == "__main__":

    # ブラウザ起動
    driver = launch_browser(userdata_dir=USERDATA_DIR, download_dir=SAVE_DIR)

    if IS_UPDATE_COURSE_LIST:
        course_list = CourseList.from_manaba(driver)
        course_list.to_json(COURSE_LIST_JSON_PATH)
    else:
        course_list = CourseList.from_json(COURSE_LIST_JSON_PATH)

    download_content_name_list = DownloadContentNameList.from_json(
        DOWNLOAD_CONTENT_NAME_LIST_JSON_PATH)
    download_content_name_list.download_contents(driver, course_list)

    driver.quit()
