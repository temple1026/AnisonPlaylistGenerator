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


    def makeAnisonDatabase(self, path_data):
        # artist_type = ["歌手", "作詞", "作曲"]
        # music_type = ["OP", "ED", "IM", "IN"]
        
        data_name = ["anison.csv", "game.csv", "sf.csv"]
        file_paths = [i for i in glob.glob(path_data + "/**", recursive=True) if os.path.splitext(i)[-1] == ".csv"]
        
        for file_path in file_paths:
            if os.path.basename(file_path) in data_name:
                category = os.path.splitext(os.path.basename(file_path))[0]
                with sqlite3.connect(self.path_database)as con, open(file_path, "r", encoding="utf-8") as f:
                    cursor = con.cursor()
                    cursor.execute("CREATE TABLE IF NOT EXISTS '%s'('%s', '%s', '%s', '%s', '%s', '%s')" % (category, "artist", "title", "anime", "genre", "oped", "order"))

                    command = "INSERT INTO " + category + " VALUES(?, ?, ?, ?, ?, ?)"
                    
                    lines = f.readlines()
                    buffer = []
                    buffer_size = 1000

                    for i, line in tqdm(enumerate(lines[1:])):
                        if not self.run:
                            break
                        
                        self.prog_db = int((i + 1)/len(lines)*100)
            
                        *keys, = line.split(",")
                        artist, title, order, oped, anime, genre = trim(keys[7]), trim(keys[6]), trim(keys[4]), trim(keys[3]), trim(keys[2]), trim(keys[1]) 
                        
                        buffer.append([artist, title, anime, genre, oped, order])

                        if i%buffer_size == 0 or i == len(lines) - 1:
                            cursor.executemany(command, buffer)
                            buffer = []
                
                    # Delete the duplication of the database
                    cursor.executescript("""
                        CREATE TEMPORARY TABLE tmp AS SELECT DISTINCT * FROM """ + category + """;
                        DELETE FROM """ + category + """;
                        INSERT INTO """ + category + """ SELECT * FROM tmp;
                        DROP TABLE tmp;
                        """)

                    con.commit()
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
            cursor.execute("CREATE TABLE IF NOT EXISTS library(artist, title, length, path)")
            
            command = "INSERT INTO library VALUES(?, ?, ?, ?)"

            buffer = []
            for i, music_file in tqdm(enumerate(music_files)):
                self.prog_music= int((i + 1)/len(music_files)*100)

                if not self.run:
                    break

                audio, artist, title, length = self.getMusicInfo(music_file)
                
                if audio != "":

                    buffer.append(tuple([trim(artist), trim(title), length, music_file]))

                    if i % 1000 == 0 or i == len(music_files) - 1:
                        cursor.executemany(command, buffer)
                        buffer = []

            cursor.executescript("""
                CREATE TEMPORARY TABLE tmp AS SELECT DISTINCT * FROM library;
                DELETE FROM library;
                INSERT INTO library SELECT * FROM tmp;
                DROP TABLE tmp;
                """)
            
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

            for category in categories:
                if not check_categories[category]:
                    continue

                if use_key:
                    cursor.execute("SELECT DISTINCT artist FROM '%s' WHERE anime LIKE \'%%%s%%\'" % (category, trim(keyword)))
                else:
                    cursor.execute("SELECT DISTINCT artist FROM '%s'" % category)

                artist_db = cursor.fetchall()

                # Get all musics corresponding to aquired artist, then apply flatten
                artist_lib = sorted(set([artist[0] for artist in self.getInfoDB('SELECT artist FROM library', cursor)]))

                for i, artist in tqdm(enumerate(artist_lib)):
                    if not self.run:
                        break

                    self.prog_playlist = int((i + 1)/len(artist_lib)*100)

                    similarities = [difflib.SequenceMatcher(None, artist, a[0]).ratio() for a in artist_db]
                    
                    if 0 < len(similarities) and th_artist < max(similarities):
                        info_list = self.getInfoDB('SELECT * FROM library WHERE artist LIKE \'' + artist + '\'', cursor)

                        if use_key:
                            cursor.execute("SELECT DISTINCT * FROM '%s' WHERE artist LIKE \'%%%s%%\' AND anime LIKE \'%%%s%%\'" % (category, artist_db[similarities.index(max(similarities))][0], trim(keyword)))
                        else:
                            cursor.execute("SELECT DISTINCT * FROM '%s' WHERE artist LIKE \'%%%s%%\'" % (category, artist_db[similarities.index(max(similarities))][0]))

                        title_list = cursor.fetchall()

                        for info in info_list:
                            artist, title, length, path = info[0], info[1], info[2], info[3]                         

                            title_ratio = [difflib.SequenceMatcher(None, title, t[1]).ratio() for t in title_list]                
                            
                            if len(title_ratio) > 0 and th_title < max(title_ratio):
                                if duplication or (sum([(title in line[0]) for line in lines]) <= 0):
                                    t = title_list[title_ratio.index(max(title_ratio))]
                                    lines.append(['#EXTINF: ' + str(int(length)) + ', ' + title + "\n" + path, t[-1]])
            
            lines = sorted(lines, key=lambda x:x[1])
            pl.writelines('#EXTM3U \n')
            pl.writelines("\n".join([line[0] for line in lines]))


def run(path_config='./config.ini'):

    config = Config(path_config).getConfig()

    path_data = config.get('path', 'data')
    path_music = config.get('path', 'library')
    path_playlist = config.get('path', 'playlist')
    path_database = config.get('path', 'database')
    
    print("Start.")
    gen = APG(path_database)
    
    print("Adding anison information to the database. (1/3)")
    gen.makeAnisonDatabase(path_data)

    print("Adding lirary information to the database. (2/3)")
    gen.makeLibrary(path_music)

    print("Making playlist. (3/3)")
    gen.generatePlaylist(path_playlist)


if __name__ == '__main__':
    run()
