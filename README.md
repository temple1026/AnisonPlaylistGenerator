# APG : Anison Playlist Generator

## これなに

- パソコンに保存されている音楽ファイルからアニソンのプレイリストを作成するプログラムです

  - 出力されるプレイリストファイルの形式：.m3u

  - プレイリストに追加できる音楽ファイルの形式 ： .mp3, .m4a, .flac

- アニソンの情報には[AnisonGeneration](http://anison.info/)様で公開されているcsvファイルを使用します(有益なデータのご提供ありがとうございます)

## 準備

a. Pythonのファイルから実行する場合

1. git clone https://github.com/temple1026/AnisonPlaylistGenerator apg

1. cd apg

1. pip install -r requirements.txt

1. python main.py

b. 実行可能形式から実行する場合

1. Releaseから最新版をDL

1. zipファイル解凍後，exeファイルを実行

本体のDL後に，

1. AnisonGeneration様の[データダウンロードサービス](http://anison.info/data/download.html)からアニメOP/ED，ゲームOP/ED，特撮OP/EDの3つのzipファイルをDL

1. 実行する階層と同じ場所にdataという名前のフォルダを作成(実行時に自動的に作成されます)

1. DLしたzipファイルを解凍後，dataフォルダに入れる

## 使い方

1. 起動後，2段目のselectをクリック．その後，音楽ファイルが保存されているフォルダを指定(初期値はC://Users/ユーザ名/Music)

1. Generate playlist only のチェックを外す

1. Runを押して数分待つ

1. "A playlist was generated"が左下に表示されたら，Playlist/AnimeSongs.m3uにプレイリストが作成されています(AnimeSongsは自由に設定可能です)

   - 作成したプレイリスト(.m3uファイル)は音楽再生ソフトウェアで読み込んでください
   - 2回目以降はGenerate playlist onlyにチェックを入れることで，全体の処理時間を短縮できます

## その他

- 初回起動後に作成されるconfig.iniファイルを編集することで，フォルダ・ファイルのパスを変更可能です

- パラメータについて

  - Use anime title : チェックを入れ，作品名を入力することで特定の作品のプレイリストを作成

  - Categories : アニメ(anime)・ゲーム(game)・特撮(sf)を含めるかどうかを決めることができます

  - Allow duplication : チェックを外すと，同じ曲名のファイルができるだけ含まれないようにすることができます

  - Rate of title : 値を小さくすることで，曲名(xx ver)のような曲もプレイリストに含めやすくすることができます

  - Rate of artist : 値を小さくすることで，アーティスト名(人名)のような曲もプレイリストに含めやすくすることができます

  - 不具合や改善点はIssuesもしくはtwitter([@10_2rugata](https://twitter.com/10_2rugata))まで

## 履歴

- 公開 : 2020/01/22
