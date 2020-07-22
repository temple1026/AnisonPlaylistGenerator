import glob
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed

from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from tqdm import tqdm

from .common import trim, trim_reverse
from .config import Config


class APG():
    def __init__(self, path_database, logger=None):
        super(APG, self).__init__()
        self.logger = logger
        self.path_database = path_database
        self.reset()
        self.initDatabase()


    def reset(self):
        self.prog_db = 0
        self.prog_music = 0
        self.prog_playlist = 0
        self.ready = True


    def getProgress(self):
        return self.prog_db, self.prog_music, self.prog_playlist


    def stop(self):
        self.ready = False


    def getRun(self):
        return self.ready 


    def initDatabase(self):
        """
        データベースの初期化を行う関数
        """
        with sqlite3.connect(self.path_database)as con:
            cursor = con.cursor()
            cursor.executescript(
                """
                CREATE TABLE IF NOT EXISTS animes(id_anime INTEGER PRIMARY KEY, name_anime UNIQUE, id_class, id_category);
                CREATE TABLE IF NOT EXISTS relation_songs(id_anime, id_song, num_order, id_type, PRIMARY KEY(id_anime, id_song));
                CREATE TABLE IF NOT EXISTS songs(id_song INTEGER PRIMARY KEY, name_song, id_artist, UNIQUE(name_song, id_artist));
                CREATE TABLE IF NOT EXISTS artists(id_artist INTEGER PRIMARY KEY, name_artist UNIQUE);
                CREATE TABLE IF NOT EXISTS classes(id_class INTEGER PRIMARY KEY, name_class UNIQUE);
                CREATE TABLE IF NOT EXISTS types(id_type INTEGER PRIMARY KEY, name_type UNIQUE);
                CREATE TABLE IF NOT EXISTS categories(id_category INTEGER PRIMARY KEY, name_category UNIQUE);
                CREATE TABLE IF NOT EXISTS local_artists(id_local_artist INTEGER PRIMARY KEY, name_local_artist UNIQUE);
                CREATE TABLE IF NOT EXISTS local_songs(id_local_song INTEGER PRIMARY KEY, id_local_artist, id_local_file, UNIQUE(id_local_artist, id_local_file));
                CREATE TABLE IF NOT EXISTS local_files(id_local_file INTEGER PRIMARY KEY, name_song, length_file, path_file UNIQUE);
                """
            )
            con.commit()

    def getCandidate(self, target):
        """
        データベースの中のアニメやアーティスト名を取得する関数
        """

        targets = []
        if target == "anime":
            sql = "SELECT name_anime FROM animes"
        elif target == "artist":
            sql = "SELECT name_artist FROM artists"

        with sqlite3.connect(self.path_database)as con:
            cursor = con.cursor()
            cursor.execute(sql)
            targets = cursor.fetchall()

        return [t[0] for t in targets]

    def makeAnisonDatabase(self, path_data):
        """
        csvファイルからアニソンのデータベースを作成する関数
        """

        data_name = ["anison.csv", "game.csv", "sf.csv"]
        file_paths = [i for i in glob.glob(path_data + "/**", recursive=True) if os.path.splitext(i)[-1] == ".csv"]

        for file_path in file_paths:
            if not os.path.basename(file_path) in data_name:
                continue
            
            with sqlite3.connect(self.path_database)as con, open(file_path, "r", encoding="utf-8") as f:
                cursor = con.cursor()
                category = os.path.basename(file_path).replace(".csv", "")
                cursor.execute("INSERT OR IGNORE INTO categories(name_category) VALUES (?)", (category,))
                id_category = cursor.execute("SELECT id_category FROM categories WHERE name_category = ?", (category,)).fetchall()[0][0]

                lines = f.readlines()
                for i, line in tqdm(enumerate(lines[1:])):
                    self.prog_db = int((i + 1)/len(lines)*100)
        
                    *keys, = line.split(",")
                    _artist, _song, _order, _anime, _type, _class = trim(keys[7]), trim(keys[6]), trim(keys[4]), trim(keys[2]), trim(keys[3]), trim(keys[1]), 
                    cursor.execute("INSERT OR IGNORE INTO artists(name_artist) VALUES (?)", (_artist,))
                    id_artist = cursor.execute("SELECT id_artist FROM artists WHERE name_artist = ?", (_artist,)).fetchall()[0][0]
                    
                    cursor.execute("INSERT OR IGNORE INTO types(name_type) VALUES (?)", (_type,))
                    id_type = cursor.execute("SELECT id_type FROM types WHERE name_type = ?", (_type,)).fetchall()[0][0]
                    
                    cursor.execute("INSERT OR IGNORE INTO classes(name_class) VALUES (?)", (_class,))
                    id_class = cursor.execute("SELECT id_class FROM classes WHERE name_class = ?", (_class,)).fetchall()[0][0]

                    cursor.execute("INSERT OR IGNORE INTO animes(name_anime, id_class, id_category) VALUES (?, ?, ?)", (_anime, id_class, id_category,))
                    id_anime = cursor.execute("SELECT id_anime FROM animes WHERE name_anime = ?", (_anime,)).fetchall()[0][0]

                    cursor.execute("INSERT OR IGNORE INTO songs(name_song, id_artist) VALUES (?, ?)", (_song, id_artist,))
                    id_song = cursor.execute("SELECT id_song FROM songs WHERE ((name_song = ?) AND (id_artist = ?))", (_song, id_artist, )).fetchall()[0][0]

                    cursor.execute("INSERT OR IGNORE INTO relation_songs(id_anime, id_song, num_order, id_type) VALUES (?, ?, ?, ?)", (id_anime, id_song, _order, id_type,))

                con.commit()

            self.prog_db = 0


    def getMusicInfo(self, path):
        """
        パスから音楽ファイルの取得する関数
        """
        length, audio, title, artist, target = 0, "", "", "", True

        if path.endswith(".flac"):
            audio = FLAC(path)
            artist = trim(audio.get('artist', [""])[0])
            title = trim(audio.get('title', [""])[0])
            length = audio.info.length

        elif path.endswith(".mp3"):
            audio = EasyID3(path)
            artist = trim(audio.get('artist', [""])[0])
            title = trim(audio.get('title', [""])[0])
            length = MP3(path).info.length
        
        elif path.endswith(".m4a"):
            audio = MP4(path)
            artist = trim(audio.get('\xa9ART', [""])[0])
            title = trim(audio.get('\xa9nam', [""])[0])
            length = audio.info.length
        else:
            target = False

        return target, artist, title, length

    def getMusics(self, path_musics):
        """
        複数のパスから音楽ファイルの情報を取得する関数
        """
        list_musics = []
        for path_music in path_musics:
            *info, = self.getMusicInfo(path_music)
            list_musics.append([*info, path_music])

        return list_musics

    def makeLibrary(self, path_library, max_workers=16):
        """
        音楽ライブラリを作成する関数
        """
        # 指定されたフォルダ内のパスを再帰的に取得
        music_files = glob.glob(os.path.join(path_library, "**"), recursive=True)
        # 1スレッドあたりのパスの数を計算
        num_per_worker = round(len(music_files)/max_workers + 0.5)
        
        results = []
        
        # マルチスレッドによる処理開始
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # パスをmax_workersで分割し音楽情報を取得
            threads = {executor.submit(self.getMusics, music_files[idx*num_per_worker:(idx+1)*num_per_worker]) : idx for idx in range(max_workers)}
            self.logger.info((f"thread_0 to thread_{max_workers} are running."))
            self.prog_music = 10

            for idx, thread in enumerate(as_completed(threads)):
                # 各スレッドが取得した音楽情報を結合
                results.extend(thread.result())
                self.logger.info((f"thread_{idx} was done."))
                self.prog_music += 10 // max_workers

        # 取得した音楽情報をデータベースに登録する処理
        with sqlite3.connect(self.path_database) as con:
            cursor = con.cursor()
            self.logger.info("Registration started.")
            for i, result in tqdm(enumerate(results)):
                self.prog_music = int((i + 1)/len(results)*80) + 20

                if not self.ready:            
                    self.logger.info("Registration canceled")
                    break

                target, artist, title, length, path_music = result

                if target:
                    cursor.execute("INSERT OR IGNORE INTO local_artists(name_local_artist) VALUES (?)", (trim(artist),))
                    id_local_artist =  cursor.execute("SELECT id_local_artist FROM local_artists WHERE name_local_artist = ?", (trim(artist),)).fetchall()[0][0]
                    
                    cursor.execute("INSERT OR IGNORE INTO local_files(name_song, length_file, path_file) VALUES (?, ?, ?)", (trim(title), length, path_music, )).lastrowid
                    id_local_file = cursor.execute("SELECT id_local_file FROM local_files WHERE path_file = ? ", (path_music,)).fetchall()[0][0]
                    
                    cursor.execute("INSERT OR IGNORE INTO local_songs(id_local_artist, id_local_file) VALUES (?, ?)", (id_local_artist, id_local_file,)).lastrowid
            
            self.logger.info("Registration completed.")
            con.commit()


    def generatePlaylist(self, path_playlist, use_key=0, keyword="", check_categories={"anison":True, "game":True, "sf":True}):
        """
        プレイリストを生成する関数
        """
        
        categories = ["anison", "game", "sf"]
        target_category = ""
        
        # 対象のカテゴリに応じてSQL文をつくる処理
        for category in categories:
            if not check_categories[category]:
                continue
            target_category += ("(name_category == \'" + category + "\') OR ")

        if target_category == "":
            return

        target_category = target_category[:target_category.rfind(" OR ")]

        # データベースから曲リストを取得する処理
        with sqlite3.connect(self.path_database) as con:
            cursor = con.cursor()
            self.prog_playlist = 10

            phrase = {1:"AND (target_anime.name_anime LIKE \'%" + trim(keyword) + "%\')", 0:""}
            cursor.executescript(
                """
                CREATE TEMPORARY TABLE anison AS
                    -- ローカルのアーティストと対応しているアニソンアーティストの情報を取得
                    SELECT local_artists.name_local_artist, target_info.name_artist, target_info.name_song
                    FROM local_artists
                    INNER JOIN(
                        -- keywordに対応したアニソンを取得
                        SELECT target_artist.name_anime, artists.name_artist, target_artist.name_song
                        FROM artists
                        INNER JOIN(
                            -- アニソンIDからアニソン名を取得
                            SELECT target_song.name_anime, songs.name_song, songs.id_artist
                            FROM songs
                            INNER JOIN(
                                -- 番組名に対応したアニソンIDを取得
                                SELECT target_anime.name_anime, relation_songs.id_song
                                    FROM relation_songs
                                    INNER JOIN (
                                        -- カテゴリIDに対応した番組名の取得
                                        SELECT animes.id_anime, animes.name_anime
                                        FROM animes
                                        INNER JOIN (
                                            -- ユーザが選択したカテゴリIDに応じて番組を取得
                                            SELECT id_category 
                                            FROM categories 
                                            WHERE """ + target_category + """
                                        ) AS target_id ON target_id.id_category = animes.id_category
                                ) AS target_anime ON ((target_anime.id_anime = relation_songs.id_anime) """ + phrase[use_key] + """)
                            )AS target_song ON target_song.id_song = songs.id_song
                        )AS target_artist ON target_artist.id_artist = artists.id_artist
                    )AS target_info ON local_artists.name_local_artist LIKE '%'||target_info.name_artist||'%';

                DELETE FROM anison WHERE name_artist = '' OR name_local_artist = '';

                CREATE TEMPORARY TABLE files AS 
                    -- ローカルアーティストに対応するファイル情報を取得
                    SELECT target_files.name_local_artist, local_files.name_song, local_files.length_file, local_files.path_file
                    FROM local_files
                    INNER JOIN(
                        -- アニソンアーティストに対応するローカルアーティスト名とアーティストのファイルを取得
                        SELECT target_artists.name_local_artist, target_artists.id_local_file
                        FROM (SELECT name_local_artist FROM anison) AS anison_artists
                        INNER JOIN(
                            -- IDからアーティスト名を取得
                            SELECT local_artists.name_local_artist, local_songs.id_local_file
                            FROM local_songs
                            INNER JOIN local_artists ON local_artists.id_local_artist = local_songs.id_local_artist
                        )AS target_artists ON target_artists.name_local_artist = anison_artists.name_local_artist
                    )AS target_files ON target_files.id_local_file = local_files.id_local_file;
                """
            )
            self.prog_playlist = 70
            lines = cursor.execute("SELECT DISTINCT files.name_song, files.length_file, files.path_file, files.name_local_artist FROM files INNER JOIN anison ON ((files.name_song LIKE anison.name_song||'%') AND (files.name_local_artist = anison.name_local_artist))").fetchall()
            lines = [["#EXTINF: " + str(int(line[1])) + ", " + trim_reverse(line[0]) + "\n" + line[2]] for line in lines]

        # 取得した音楽情報からプレイリストを出力する処理
        with open(path_playlist, 'w', encoding='utf-16') as pl:
            pl.writelines('#EXTM3U \n')
            pl.writelines("\n".join([line[0] for line in lines]))
            self.prog_playlist = 100


def run(path_config='./config.ini', logger=None):

    config = Config(path_config).getConfig()

    path_data = config.get('path', 'data')
    path_music = config.get('path', 'library')
    path_playlist = config.get('path', 'playlist')
    path_database = config.get('path', 'database')
    
    print("Start.")
    print(path_database)
    gen = APG(path_database, logger=logger)
    
    print("Adding anison information to the database. (1/3)")
    gen.makeAnisonDatabase(path_data)

    print("Adding lirary information to the database. (2/3)")
    gen.makeLibrary(path_music)

    print("Making playlist. (3/3)")
    gen.generatePlaylist(path_playlist)


if __name__ == '__main__':
    run()
