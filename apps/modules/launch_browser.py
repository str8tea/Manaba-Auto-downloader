from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager


def launch_browser(userdata_dir: Path, download_dir: Path = None) -> WebDriver:
    """ユーザーデータをもつChromeを起動する

    Args:
        userdata_dir(Path): Chromeのユーザーデータディレクトリがある場所
        download_dir(Path, optional): ダウンロード先のディレクトリ（デフォルト値はNone）

    Note:
        download_dirのパスの区切り文字に'/'は無効、'\\'かr文字列で指定すること('\\'の場合は、ルートの区切りのみ'\')
        （参照：https://qiita.com/hikoalpha/items/fa8330391823aea2fbca）
        download_dirがNoneの場合は、C:/Users/username/downloadsのまま
        headlessモードではWebページにアクセスできない（参照：https://qiita.com/memakura/items/dbe7f6edadd456da1c5d）

    Returns:
        selenium.webdriver.chrome.webdriver.WebDriver: Chromeを操作するWeDriverインスタンス
    """

    # ユーザーデータの設定
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f"--user-data-dir={userdata_dir}")

    # ダウンロード先のディレクトリの設定（参照：https://www.microfocus.com/documentation/silk-test/195/ja/silk4net-195-help-ja/GUID-781614F2-54A0-4BE3-95B9-C282121A9B43.html）
    if download_dir:
        chrome_options.add_experimental_option(
            "prefs", {
                "profile.default_content_setting_values.automatic_downloads": 1,
                "download.default_directory": str(download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True})

    # その他の各設定を行う
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--start-maximized")  # 起動時にウィンドウを最大化する
    # "enable-automation":「Chromeは自動テストソフトウェアによって制御されています」の表示を削除
    # "enable-logging": # 関係ないログを非表示にする（参照：https://miya-mitsu.com/python-0x1ferror/）
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation", "enable-logging"])

    # GoogleChromeを起動（ChromeDriverManagerでChromeのバージョンに合うwebドライバーをインストールして起動）
    # 参照：https://qiita.com/hanzawak/items/2ab4d2a333d6be6ac760
    driver = webdriver.Chrome(
        ChromeDriverManager().install(), options=chrome_options)
    driver.implicitly_wait(5)  # 暗黙的な待機時間を設定する（findメソッドの待機時間）
    driver.set_page_load_timeout(10)  # ページの最大読み込み時間を設定（超えると例外が発生）

    return driver
