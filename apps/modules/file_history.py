from __future__ import annotations
from dataclasses import dataclass, asdict
import json
from pathlib import Path

from .file_metadata import FileMetadata


@dataclass(frozen=True, slots=True)
class FileHistory:
    """ダウンロードしたファイルの履歴（メタデータ）を表すデータクラス

    履歴にファイルのメタデータの追加、履歴をJSONファイルに書き込みを行う

    Note:
        JSONファイルから読み込んで生成されることを想定
    """

    file_history: list[FileMetadata]

    @classmethod
    def from_json(cls, json_path: Path) -> FileHistory:
        """JSONファイルから自身のインスタンスを生成

        Args:
            json_path (Path): ファイルの履歴があるJSONファイルパス

        Returns:
            FileHistory: ファイルのメタデータのリスト（ファイルの履歴がない場合は空リスト）を引数とする自身のインスタンス
        """

        # JSONファイルがない場合は新規作成する
        json_path.touch(exist_ok=True)

        # JSONファイルの中身が空の場合
        if json_path.stat().st_size == 0:
            return cls([])

        # JSONファイルからダウンロードしたファイルの履歴を辞書形式で読み取る
        with open(json_path, "r", encoding='utf-8') as f:
            file_metadata_dict_list = json.load(f)

        # 辞書型のファイルが入るリストをFileMetadata型のファイルが入るリストに変換する
        file_history = [FileMetadata(**file_dict)
                        for file_dict in file_metadata_dict_list]

        return cls(file_history)

    def add(self, file_metadata: FileMetadata):
        """引数のファイルのメタデータを履歴の先頭に加える

        Args:
            file_metadata (FileMetadata): ファイルのメタデータ
        """
        self.file_history.insert(0, file_metadata)

    def to_json(self, json_path: Path) -> None:
        """ファイルの履歴をJSONファイルに書き込む（上書き）

        Args:
            json_path (Path): 書き込み先のJSONファイルパス
        """

        # FileMetadata型のファイルが入るリストを辞書型のファイルが入るリストに変換する
        file_metadata_dict_list = [
            asdict(file_metadata) for file_metadata in self.file_history]

        with open(json_path, "w", encoding="utf-8") as f:
            # JSON形式でファイルに書き込む
            json.dump(file_metadata_dict_list, f, ensure_ascii=False)
