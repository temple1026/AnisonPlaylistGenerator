import argparse
import csv
import difflib
import glob
import os
import re
import sqlite3
import threading
from itertools import chain

from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from tqdm import tqdm

from .common import trim
from .config import Config

class APG():
    def __init__(self, path_database):
        super(APG, self).__init__()
        self.path_database = path_database
        self.reset()


    def reset(self):
        self.prog_db = 0
        self.prog_music = 0
        self.prog_playlist = 0
        self.run = True


    def getProgress(self):
        return self.prog_db, self.prog_music, self.prog_playlist


    def stop(self):
        self.run = False


    def getRun(self):
        return self.run 

    def initDatabase(self):
        commands = [
            "CREATE TABLE IF NOT EXISTS animes(id_anime INTEGER PRIMARY KEY, name_anime UNIQUE, id_class, id_category)", 
            "CREATE TABLE IF NOT EXISTS relation_songs(id_anime, id_song, num_order, id_type, PRIMARY KEY(id_anime, id_song))",
            "CREATE TABLE IF NOT EXISTS songs(id_song INTEGER PRIMARY KEY, name_song, id_artist, UNIQUE(name_song, id_artist))",
            "CREATE TABLE IF NOT EXISTS artists(id_artist INTEGER PRIMARY KEY, name_artist UNIQUE)",
            "CREATE TABLE IF NOT EXISTS classes(id_class INTEGER PRIMARY KEY, name_class UNIQUE)",
            "CREATE TABLE IF NOT EXISTS types(id_type INTEGER PRIMARY KEY, name_type UNIQUE)",
            "CREATE TABLE IF NOT EXISTS categories(id_category INTEGER PRIMARY KEY, name_category UNIQUE)",
            "CREATE TABLE IF NOT EXISTS local_artists(id_local_artist INTEGER PRIMARY KEY, name_local_artist UNIQUE)",
            "CREATE TABLE IF NOT EXISTS local_musics(id_local_music INTEGER PRIMARY KEY, id_local_artist, id_local_file, UNIQUE(id_local_artist, id_local_file))",
            "CREATE TABLE IF NOT EXISTS local_files(id_local_file INTEGER PRIMARY KEY, name_song, length_file, path_file UNIQUE)",
        ]

        with sqlite3.connect(self.path_database)as con:
            cursor = con.cursor()
            
            for command in commands:
                cursor.execute(command)
            con.commit()

            

    def makeAnisonDatabase(self, path_data):
        # artist_type = ["歌手", "作詞", "作曲"]
        # music_type = ["OP", "ED", "IM", "IN"]
        
        data_name = ["anison.csv", "game.csv", "sf.csv"]
        file_paths = [i for i in glob.glob(path_data + "/**", recursive=True) if os.path.splitext(i)[-1] == ".csv"]

        if os.path.exists(self.path_database):
            os.remove(self.path_database)
        self.initDatabase()

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
                
        # for file_path in file_paths:
        #     if os.path.basename(file_path) in data_name:
        #         category = os.path.splitext(os.path.basename(file_path))[0]
        #         with sqlite3.connect(self.path_database)as con, open(file_path, "r", encoding="utf-8") as f:
        #             cursor = con.cursor()
        #             cursor.execute("CREATE TABLE IF NOT EXISTS '%s'('%s', '%s', '%s', '%s', '%s', '%s')" % (category, "artist", "title", "anime", "genre", "oped", "order"))

        #             command = "INSERT INTO " + category + " VALUES(?, ?, ?, ?, ?, ?)"
                    
        #             lines = f.readlines()
        #             buffer = []
        #             buffer_size = 1000

        #             for i, line in tqdm(enumerate(lines[1:])):
        #                 if not self.run:
        #                     break
                        
        #                 self.prog_db = int((i + 1)/len(lines)*100)
            
        #                 *keys, = line.split(",")
        #                 artist, title, order, oped, anime, genre = trim(keys[7]), trim(keys[6]), trim(keys[4]), trim(keys[3]), trim(keys[2]), trim(keys[1]) 
                        
        #                 buffer.append([artist, title, anime, genre, oped, order])

        #                 if i%buffer_size == 0 or i == len(lines) - 1:
        #                     cursor.executemany(command, buffer)
        #                     buffer = []
                
        #             # Delete the duplication of the database
        #             cursor.executescript("""
        #                 CREATE TEMPORARY TABLE tmp AS SELECT DISTINCT * FROM """ + category + """;
        #                 DELETE FROM """ + category + """;
        #                 INSERT INTO """ + category + """ SELECT * FROM tmp;
        #                 DROP TABLE tmp;
        #                 """)

        #             con.commit()
            self.prog_db = 0

    def getMusicInfo(self, path):
        """
        Decode music file.
        """
        length, audio, title, artist = 0, "", "", ""
        
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
        
        return audio, artist, title, length


    def outputArtist(self):
        with open('artist_list.txt', 'w', encoding='utf-8') as writer, sqlite3.connect(self.path_database) as con:
            cursor = con.cursor()
            cursor.execute('SELECT DISTINCT artist FROM library')
            artist_list = cursor.fetchall()
            
            for artist in artist_list:
                writer.writelines(artist[0] + "\n")


    def makeLibrary(self, path_music):
        music_files = glob.glob(path_music + "/**", recursive=True)

        with sqlite3.connect(self.path_database) as con:
            cursor = con.cursor()
            self.initDatabase()
            for i, music_file in tqdm(enumerate(music_files)):
                self.prog_music= int((i + 1)/len(music_files)*100)

                if not self.run:
                    break

                audio, artist, title, length = self.getMusicInfo(music_file)
                
                if audio != "":
                    cursor.execute("INSERT OR IGNORE INTO local_artists(name_local_artist) VALUES (?)", (trim(artist),))
                    id_local_artist =  cursor.execute("SELECT id_local_artist FROM local_artists WHERE name_local_artist = ?", (trim(artist),)).fetchall()[0][0]
                    
                    cursor.execute("INSERT OR IGNORE INTO local_files(name_song, length_file, path_file) VALUES (?, ?, ?)", (trim(title), length, music_file, )).lastrowid
                    id_local_file = cursor.execute("SELECT id_local_file FROM local_files WHERE path_file = ? ", (music_file,)).fetchall()[0][0]
                    
                    cursor.execute("INSERT OR IGNORE INTO local_musics(id_local_artist, id_local_file) VALUES (?, ?)", (id_local_artist, id_local_file,)).lastrowid
                    # print(artist, id_local_artist, id_local_file)
            con.commit()

    def getInfoDB(self, command, cursor):
        cursor.execute(command)
        return cursor.fetchall()

        
    def generatePlaylist(self, path_playlist, use_key=False, keyword="", th_title=0.55, th_artist=0.8, 
                         duplication=False, check_categories={"anison":True, "game":True, "sf":True}):
        """
        Generate playlist from database.
        """
        with open(path_playlist, 'w', encoding='utf-16') as pl, sqlite3.connect(self.path_database) as con:
            lines = []
            cursor = con.cursor()

            categories = ["anison", "game", "sf"]
            target_category = ""
            
            for category in categories:
                if not check_categories[category]:
                    continue
                target_category += ("(name_category == \'" + category + "\') OR ")

            if target_category == "":
                return

            target_category = target_category[:target_category.rfind(" OR ")]

            cursor.executescript(
                """
                -- カテゴリに対応するアニメを抽出
                CREATE TEMPORARY TABLE tmp AS SELECT id_anime, name_anime FROM animes INNER JOIN (SELECT id_category FROM categories WHERE (""" + target_category + """)) AS cat_id ON cat_id.id_category = animes.id_category;
                -- アニメに対応する楽曲を抽出
                CREATE TEMPORARY TABLE tmp1 AS SELECT id_song FROM relation_songs INNER JOIN tmp ON tmp.id_anime = relation_songs.id_anime;
                -- アニソンに対応するアーティストidを抽出
                CREATE TEMPORARY TABLE tmp2 AS SELECT name_song, id_artist FROM songs INNER JOIN tmp1 ON tmp1.id_song = songs.id_song;
                -- アーティスト名とアーティストidを抽出
                CREATE TEMPORARY TABLE tmp3 AS SELECT tmp2.id_artist, artists.name_artist, tmp2.name_song FROM artists INNER JOIN tmp2 ON tmp2.id_artist = artists.id_artist;
                -- ローカルアーティストidとアニソンアーティストidの対応をつける
                CREATE TEMPORARY TABLE tmp4 AS SELECT DISTINCT id_artist, name_artist, id_local_artist, name_local_artist FROM local_artists INNER JOIN tmp3 ON local_artists.name_local_artist LIKE '%'||tmp3.name_artist||'%';
                -- アーティスト名のないレコードを削除
                DELETE FROM tmp4 WHERE name_artist = '';
                
                CREATE TEMPORARY TABLE tmp5 AS SELECT id_local_file, name_artist FROM local_musics INNER JOIN tmp4 ON tmp4.id_local_artist = local_musics.id_local_artist;
                CREATE TEMPORARY TABLE tmp6 AS SELECT DISTINCT name_artist, name_song, length_file, path_file FROM local_files INNER JOIN tmp5 ON tmp5.id_local_file = local_files.id_local_file;
                CREATE TEMPORARY TABLE tmp7 AS SELECT name_song, name_artist FROM songs INNER JOIN tmp4 ON tmp4.id_artist = songs.id_artist; 
                CREATE TEMPORARY TABLE tmp8 AS SELECT DISTINCT tmp6.name_song, length_file, path_file FROM tmp6 INNER JOIN tmp7 ON ((tmp6.name_song LIKE '%'||tmp7.name_song||'%') AND (tmp6.name_artist = tmp7.name_artist)); 
                """
            )

            # cursor.execute("SELECT length_file, name_song, path_file FROM tmp8")
            # cursor.execute("SELECT * FROM tmp8 ORDER BY name_song DESC LIMIT 20")
            # cursor.execute("SELECT * FROM tmp5")
            # cursor.execute("SELECT * FROM local_artists ORDER BY name_local_artist")
            cursor.execute("SELECT * FROM tmp8")
            lines = cursor.fetchall()
            lines = [["#EXTINF: " + str(int(line[1])) + ", " + line[0] + "\n" + line[2]] for line in lines]

            print(lines)

            # cursor.execute("SELECT * FROM tmp4")
            # cursor.execute("SELECT * FROM local_artists ORDER BY name_local_artist")

            # result = cursor.fetchall()
            # for idx, r in enumerate(result):
            #     print(idx, r)
            # # print(result)

            # cursor.execute("SELECT id_anime FROM animes INNER JOIN categories ON animes.id_category = (SELECT id_category FROM categories WHERE name_category = \'" + category + "\');")
                
            # for category in categories:
            #     if not check_categories[category]:
            #         continue

            #     if use_key:
            #         cursor.execute("SELECT DISTINCT artist FROM '%s' WHERE anime LIKE \'%%%s%%\'" % (category, trim(keyword)))
            #     else:
            #         cursor.execute("SELECT DISTINCT artist FROM '%s'" % category)

            #     artist_db = cursor.fetchall()

            #     # Get all musics corresponding to aquired artist, then apply flatten
            #     artist_lib = sorted(set([artist[0] for artist in self.getInfoDB('SELECT artist FROM library', cursor)]))

            #     for i, artist in tqdm(enumerate(artist_lib)):
            #         if not self.run:
            #             break

            #         self.prog_playlist = int((i + 1)/len(artist_lib)*100)

            #         similarities = [difflib.SequenceMatcher(None, artist, a[0]).ratio() for a in artist_db]
                    
            #         if 0 < len(similarities) and th_artist < max(similarities):
            #             info_list = self.getInfoDB('SELECT * FROM library WHERE artist LIKE \'' + artist + '\'', cursor)

            #             if use_key:
            #                 cursor.execute("SELECT DISTINCT * FROM '%s' WHERE artist LIKE \'%%%s%%\' AND anime LIKE \'%%%s%%\'" % (category, artist_db[similarities.index(max(similarities))][0], trim(keyword)))
            #             else:
            #                 cursor.execute("SELECT DISTINCT * FROM '%s' WHERE artist LIKE \'%%%s%%\'" % (category, artist_db[similarities.index(max(similarities))][0]))

            #             title_list = cursor.fetchall()

            #             for info in info_list:
            #                 artist, title, length, path = info[0], info[1], info[2], info[3]                         

            #                 title_ratio = [difflib.SequenceMatcher(None, title, t[1]).ratio() for t in title_list]                
                            
            #                 if len(title_ratio) > 0 and th_title < max(title_ratio):
            #                     if duplication or (sum([(title in line[0]) for line in lines]) <= 0):
            #                         t = title_list[title_ratio.index(max(title_ratio))]
            #                         lines.append(['#EXTINF: ' + str(int(length)) + ', ' + title + "\n" + path, t[-1]])
            
            # lines = sorted(lines, key=lambda x:x[1])
            pl.writelines('#EXTM3U \n')
            pl.writelines("\n".join([line[0] for line in lines]))


def run(path_config='./config.ini'):

    config = Config(path_config).getConfig()

    path_data = config.get('path', 'data')
    path_music = config.get('path', 'library')
    path_playlist = config.get('path', 'playlist')
    path_database = config.get('path', 'database')
    
    print("Start.")
    print(path_database)
    gen = APG(path_database)
    
    # print("Adding anison information to the database. (1/3)")
    # gen.makeAnisonDatabase(path_data)

    # print("Adding lirary information to the database. (2/3)")
    # gen.makeLibrary(path_music)

    print("Making playlist. (3/3)")
    gen.generatePlaylist(path_playlist)
    
if __name__ == '__main__':
    run()
