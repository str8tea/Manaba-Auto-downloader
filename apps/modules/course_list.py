from __future__ import annotations
from dataclasses import asdict
import json

from bs4 import BeautifulSoup
from selenium.webdriver.chrome.webdriver import WebDriver

from .course import Course
from .go_manaba import go_manaba


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

        Returns:
            Content: 目的の講義（見つからなかった場合や複数ある場合はNone）

        Note:
            引数の名前を含む講義が複数ある場合はNoneとする
            ただし、引数の名前の講義がある場合は、その講義を返す
            ex) 講義の一覧に'情報工学'と'情報工学実験'の2つがある場合、'情報工学'で検索したら、'情報工学'の講義を返す

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
