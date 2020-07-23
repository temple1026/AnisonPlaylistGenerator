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

1. zipファイルを解凍

本体のDL後に，

1. AnisonGeneration様の[データダウンロードサービス](http://anison.info/data/download.html)からアニメOP/ED，ゲームOP/ED，特撮OP/EDの3つのzipファイルをDL

1. 実行する階層と同じ場所にdataという名前のフォルダを作成(実行時に自動的に作成されます)

1. DLしたzipファイルを解凍後，dataフォルダに入れる

## 使い方

1. 起動後，DLしたcsvファイルがあるフォルダ，パソコン内の音楽ライブラリまでのパス，プレイリストの出力先のパスを環境にあわせて修正する

1. DB更新を押し，データベースを更新する
 
1. 実行を押す
  - 実行ボタンが再度押せるようになったら作成完了です
  - 作成したプレイリスト(.m3uファイル)は音楽再生ソフトウェアで読み込んでください
   
## その他

- 初回起動後に作成されるconfig.iniファイルを編集することで，フォルダ・ファイルのパスを変更可能です

- データベース更新は次の場合に実行してください
  - 初回起動時
  - csvファイルを入れ替えたとき
  - 音楽ライブラリに新しいファイルを追加したとき
  
- 作品名にチェックを入れることで，特定の作品のプレイリストを作ることができます

- 不具合や改善点はIssuesもしくはtwitter([@10_2rugata](https://twitter.com/10_2rugata))まで

## 履歴
- v0.3公開 : 2020/07/23
- 公開 : 2020/01/22
