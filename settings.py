import json
import urllib.parse
from pathlib import Path

TOP_DIR = Path(__file__).resolve().parent
CONFIG_DIR = TOP_DIR / "config"
OUTPUT_DIR = TOP_DIR / "output"

SETTINGS_PATH = CONFIG_DIR / "settings.json"

# 設定ファイル(json)から各要素を読み取る
with open(SETTINGS_PATH, "r", encoding='utf-8') as f:
    settings = json.load(f)

# manabaのホームページのURL
MANABA_HOME_URL = settings["manaba_home_url"]

# MANABA_HOME_URLからmanabaのクライアントURLを作成する
manaba_home_url_tuples = urllib.parse.urlsplit(MANABA_HOME_URL)
base_url = f"{manaba_home_url_tuples.scheme}://{manaba_home_url_tuples.netloc}"
url_path = manaba_home_url_tuples.path
client_path = url_path.rpartition("/")[0] + "/"
MANABA_CLIENT_URL = urllib.parse.urljoin(base_url, client_path)

# Chromeのユーザーデータのフォルダがある場所
if settings["is_absolute_userdata_path"]:
    USERDATA_DIR = Path(settings["userdata_dir"])
else:
    USERDATA_DIR = TOP_DIR / Path(settings["userdata_dir"])

# ダウンロードしたファイルの保存先のディレクトリ
SAVE_DIR = Path(settings["save_dir"])
# ダウンロードしたファイルの履歴が入るJSONファイルのパス
FILE_HISTORY_JSON_PATH = OUTPUT_DIR / "file_history.json"
# 講義の一覧が保存されるJSONファイルのパス
COURSE_LIST_JSON_PATH = OUTPUT_DIR / "course_list.json"
# ダウンロードするコンテンツ名の一覧が入るJSONファイルのパス
DOWNLOAD_CONTENT_LIST_JSON_PATH = CONFIG_DIR / "download_content_list.json"

# 講義の一覧（COURSE_LIST_JSON_PATH）を更新するかしないか（True or False）
IS_UPDATE_COURSE_LIST = settings["is_update_course_list"]
