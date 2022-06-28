from __future__ import annotations
from dataclasses import dataclass

from bs4 import BeautifulSoup

from settings import MANABA_CLIENT_URL


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
        full_link = MANABA_CLIENT_URL + link
        update_date = header.find("span").get_text()

        return cls(name, full_link, update_date)
