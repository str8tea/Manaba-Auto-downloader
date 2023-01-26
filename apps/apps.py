# manabaから講義資料を自動でダウンロードするプログラム

from __future__ import annotations
import sys
from pathlib import Path

# manaba_auto_downloaderディレクトリをモジュール検索パスに追加（そのディレクトリにあるsettings.pyがインポート可能になる）
sys.path.append(str(Path(__file__).parents[1]))  # noqa: E402

import modules
from settings import USERDATA_DIR, SAVE_DIR, COURSE_LIST_JSON_PATH, DOWNLOAD_CONTENT_LIST_JSON_PATH, FILE_HISTORY_JSON_PATH, IS_UPDATE_COURSE_LIST

if __name__ == "__main__":

    # 必要なファイルの作成
    Path(COURSE_LIST_JSON_PATH).touch(exist_ok=True)
    Path(FILE_HISTORY_JSON_PATH).touch(exist_ok=True)

    # ブラウザ起動
    driver = modules.launch_browser(
        userdata_dir=USERDATA_DIR, download_dir=str(SAVE_DIR))

    # 講義の一覧を更新する
    if IS_UPDATE_COURSE_LIST:
        # manabaのホームページからスクレイピングをして、講義の一覧を取得する
        course_list = modules.CourseList.from_manaba(driver)
        # 取得した講義の一覧をJSONファイルに保存する
        course_list.to_json(COURSE_LIST_JSON_PATH)
    else:
        # JSONファイルから講義の一覧を取得する
        course_list = modules.CourseList.from_json(COURSE_LIST_JSON_PATH)

    # ダウンロードするコンテンツの名前の一覧から該当のコンテンツにある未読の添付ファイルをダウンロードする
    download_content_list = modules.DownloadContentList.from_json(
        DOWNLOAD_CONTENT_LIST_JSON_PATH)
    download_content_list.download_contents(driver, course_list)

    # ブラウザを終了する
    driver.quit()
