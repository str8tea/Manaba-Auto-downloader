# manabaから講義資料を自動でダウンロードするプログラム

from __future__ import annotations
import os
import sys

# manaba_auto_downloaderディレクトリをモジュール検索パスに追加（そのディレクトリにあるsettings.pyをインポートするため）
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))  # noqa: E402

import modules
from settings import USERDATA_DIR, SAVE_DIR, COURSE_LIST_JSON_PATH, DOWNLOAD_CONTENT_NAME_LIST_JSON_PATH, IS_UPDATE_COURSE_LIST

if __name__ == "__main__":
    # ブラウザ起動
    driver = modules.launch_browser(
        userdata_dir=USERDATA_DIR, download_dir=SAVE_DIR)

    # 講義の一覧を更新する
    if IS_UPDATE_COURSE_LIST:
        course_list = modules.CourseList.from_manaba(driver)
        course_list.to_json(COURSE_LIST_JSON_PATH)
    else:
        course_list = modules.CourseList.from_json(COURSE_LIST_JSON_PATH)

    # ダウンロードするコンテンツの名前の一覧から該当のコンテンツにある未読の添付ファイルをダウンロードする
    download_content_name_list = modules.DownloadContentNameList.from_json(
        DOWNLOAD_CONTENT_NAME_LIST_JSON_PATH)
    download_content_name_list.download_contents(driver, course_list)

    # ブラウザを終了する
    driver.quit()
