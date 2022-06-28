# Manaba Auto-downloader
## このプログラムは開発者の実行環境でしか実行できません！
## このプログラムはインターンシップ選考のための成果物です。
---

# OverView
manabaというクラウド型教育支援システムから講義資料を自動でダウンロードするプログラムです。   
このプログラムを実行すると、Chromeブラウザが起動し、manabaのホームページに移動してスクレイピングを行います。そのスクレイピングした情報をもとに講義資料をダウンロードします。
 
# DEMO
 
Comming soon...
 
# Features
 
このプログラムを実行すると、講義資料を自動でダウンロードしてくれるため、講義前にmanabaにアクセスして講義資料をいちいちダウンロードする手間が省けます。
 
# Requirement
言語
* Python 3.10.2

必要なライブラリ
* bs4 0.0.1
* selenium 4.2.0
* webdriver-manager 3.5.2

その他
* manabaのユーザIDとパスワードが保存されているChromeのユーザーデータ

# Installation
 
```bash
pip install beautifulsoup4
pip install selenium
pip install webdriver-manager

```
 
# Usage

1. 下記のコマンドを実行して、クローンする
```bash
git clone https://github.com/str8tea/manaba_auto_downloader.git
```
2. settings.jsonを編集して各種設定を行う
1. download_content_list.jsonに自動でダウンロードしたい講義資料の講義の名前とコンテンツの名前を指定する
1. 下記のコマンドを実行して、プログラムを実行する
```bash
python3 manaba_auto_downloader\apps\apps.py
```
 
# Note

このプログラムの実行には、manabaのユーザIDとパスワードが保存されているChromeのユーザーデータが必要です。 また、著者が通っている大学と同じ大学のmanabaでしか動作は保証されません。

 