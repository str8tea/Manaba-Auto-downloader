from __future__ import annotations
from dataclasses import dataclass
import json

from .course_list import CourseList
from .download_content_name import DownloadContentName


@dataclass(frozen=True, slots=True)
class DownloadContentNameList:
    """ダウンロードするコンテンツの名前の一覧を表すデータクラス

    Note :
        JSONファイルから読み込んで生成されることを想定
    """

    content_name_list: list[DownloadContentName]

    @classmethod
    def from_json(cls, json_filename: str) -> DownloadContentNameList:
        """JSONファイルから自身のインスタンスを生成する

        Args:
            json_filename (str): ダウンロードするコンテンツの名前の一覧があるJSONファイルの名前

        Returns:
            DownloadContentNameList: コンテンツの名前の一覧を引数とする自身のインスタンス
        """

        with open(json_filename, "r", encoding='utf-8') as f:
            content_name_dict_list = json.load(f)  # JSONデータを辞書形式で読み取る

        # 辞書型のダウンロードするコンテンツの名前が入るリストをDownloadContentName型の名前が入るリストに変換する
        content_name_list = [DownloadContentName(
            **content_name_dict) for content_name_dict in content_name_dict_list]

        return cls(content_name_list)

    def download_contents(self, driver, course_list: CourseList):
        """メンバ変数のコンテンツの名前から、コンテンツ内の未読ページにある添付ファイルをダウンロードする

        Args:
            driver (Webdriver): ブラウザを操作するドライバー（Selenium）
            course_list (CourseList): 講義の一覧
        """
        for content_name in self.content_name_list:
            content_name.download_content(driver, course_list)
