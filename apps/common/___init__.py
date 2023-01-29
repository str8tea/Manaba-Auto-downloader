import sys
from pathlib import Path
# manaba_auto_downloaderディレクトリをモジュール検索パスに追加（そのディレクトリにあるsettings.pyがインポート可能になる）
sys.path.append(str(Path(__file__).parents[1]))  # noqa: E402
