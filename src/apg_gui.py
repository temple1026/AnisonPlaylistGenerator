import os
import sys
import time

from PyQt5.QtCore import QRect, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import (QApplication, QCheckBox, QFileDialog, QLabel,
                             QLineEdit, QProgressBar, QPushButton, QSpinBox,
                             QStatusBar, QWidget, QMessageBox, QCompleter)

from .apg import APG
from .config import Config
from .sentence import LANG_ENG, LANG_JA


class SubProgress(QThread):
    """
    プログレスバーの更新用のクラス
    """
    signal = pyqtSignal(int)
    running = True

    def run(self):
        self.running=True
        while self.running:
            time.sleep(0.01)
            self.signal.emit(0)

    def wait(self):
        self.running = False

class UpdateDB(QThread):
    """
    データベースの更新をバックグラウンドで行うためのクラス
    """
    signal = pyqtSignal(str)
    running = True

    def __init__(self, parent=None, apg=APG("info.db"), path_data="", path_library=""):
        super(UpdateDB, self).__init__()
        self.apg = apg
        self.path_data = path_data
        self.path_library = path_library

    def run(self):
        if self.running:
            self.signal.emit("アニソンデータの更新中．")
            self.apg.makeAnisonDatabase(self.path_data)
        
        if self.running:
            self.signal.emit("ライブラリの更新中．")
            self.apg.makeLibrary(self.path_library)

        self.signal.emit("")
        return
    
    def wait(self):
        self.apg.stop()
        self.running = False

class GenPlaylist(QThread):
    """
    プレイリストの作成をバックグラウンドで処理するためのクラス
    """
    signal = pyqtSignal(str)
    running = True

    def __init__(self, parent=None, apg=APG("info.db"), use_key=0, path_playlist="", keyword = "", check_categories={"anison":True, "game":True, "sf":True}):
        super(GenPlaylist, self).__init__()
        self.apg = apg
        self.path_playlist = path_playlist
        self.keyword = keyword
        self.check_categories = check_categories
        self.use_key = use_key

    def run(self):
        self.signal.emit("プレイリストの作成中．")
        self.apg.generatePlaylist(self.path_playlist, self.use_key, self.keyword, self.check_categories)
        self.signal.emit("")    
        return
    
    def wait(self):
        self.apg.stop()

class MainWindow(QWidget):
    def __init__(self, parent=None, path_config='config.ini', path_style='./styles/style.qss', logger=None):
        super(MainWindow, self).__init__(parent)
        self.path_config = path_config
        self.config = Config(self.path_config)
        self.settings = self.config.getConfig()
        self.logger = logger
        self.drawInitialMenu(path_style)


    def drawInitialMenu(self, path_style='./styles/style.qss'):
        self.path_to_data = self.settings.get('path', 'data')
        self.path_to_library = self.settings.get('path', 'library')
        self.path_to_playlist = self.settings.get('path', 'playlist')
        self.path_to_database = self.settings.get('path', 'database')
        
        self.language = self.settings.get('general', 'language')
        self.style = self.settings.get('general', 'style')

        try:        
            with open(path_style, "r") as f:
                stylesheet = f.read()
        except:
            stylesheet = '''
                    QWidget{background-color: #f0f8ff; color:#0f0f7f}
                    QPushButton{color: #ffffff;  background-color: #7070ff; border: 2px; border-radius: 5px; font-weight:bold}
                    QPushButton:hover,QPushButton:pressed{color: #ffffff; background-color:#9f9f9f}
                    QPushButton:disabled{color: #ffffff; background-color:#dfdfdf}
                    QLineEdit{color:#0f0f7f; border:1px solid #a0a0a0; border-radius: 5px; background-color:#dff3ff}
                    QLineEdit:hover{color:#0f0f7f; border:1px solid #7070ff; border-radius: 5px}
                    QLineEdit:disabled{color:#d0d0d0; border:1px solid #d0d0d0; border-radius: 5px}
                    QSpinBox{color:#0f0f7f; border:1px solid #a0a0a0; border-radius: 5px; background-color:#dff3ff}
                    QSpinBox:hover{color:#0f0f7f; border:1px solid #7070ff; border-radius: 5px}
                    QProgressBar{text-align:center; color:#7f7faf; font-weight:bold}
                    QProgressBar::chunk{background-color: #50ff50; width: 10px; margin: 1px;}
                    '''
        
        self.setStyleSheet(stylesheet)

        if self.language == "en":
            self.sentences = LANG_ENG
        else:
            self.sentences = LANG_JA

        self.apg = APG(self.path_to_database, self.logger)
        
        self.width = int(self.settings.get('screen', 'width'))
        self.height = int(self.settings.get('screen', 'height'))
        
        self.label_data = QLabel(self.sentences["path_to_data"], self)
        self.label_data.setGeometry(self.width*0.08, self.height*0.10, self.width*0.2, 30)

        self.label_library = QLabel(self.sentences["path_to_library"], self)
        self.label_library.setGeometry(self.width*0.08, self.height*0.20, self.width*0.2, 30)

        self.label_playlist = QLabel(self.sentences["path_to_playlist"], self)
        self.label_playlist.setGeometry(self.width*0.08, self.height*0.30, self.width*0.2, 30)

        self.label_advanced = QLabel(self.sentences["advanced_settings"], self)
        self.label_advanced.setGeometry(self.width*0.08, self.height*0.40, self.width*0.22, 30)

        self.setFixedSize(self.width, self.height)

        self.button_data = QPushButton(self.sentences["select"], self)
        self.button_data.setObjectName('path_data')
        self.button_data.setGeometry(self.width*0.78, self.height*0.10, self.width*0.15, 30)
        self.button_data.clicked.connect(self.buttonClicked) 

        self.button_library = QPushButton(self.sentences["select"], self)
        self.button_library.setObjectName('path_library')
        self.button_library.setGeometry(self.width*0.78, self.height*0.20, self.width*0.15, 30)
        self.button_library.clicked.connect(self.buttonClicked) 

        self.button_playlist = QPushButton(self.sentences["select"], self)
        self.button_playlist.setObjectName('path_playlist')
        self.button_playlist.setGeometry(self.width*0.78, self.height*0.30, self.width*0.15, 30)
        self.button_playlist.clicked.connect(self.buttonClicked) 

        self.line_data = QLineEdit(self.path_to_data, self)
        self.line_data.setGeometry(self.width*0.27, self.height*0.10, self.width*0.5, 30)
        self.line_data.setToolTip(self.sentences["tips_data"])
        
        self.line_library = QLineEdit(self.path_to_library, self)
        self.line_library.setGeometry(self.width*0.27, self.height*0.20, self.width*0.5, 30)
        self.line_library.setToolTip(self.sentences["tips_library"])
        
        self.line_playlist = QLineEdit(self.path_to_playlist, self)
        self.line_playlist.setGeometry(self.width*0.27, self.height*0.30, self.width*0.5, 30)
        self.line_playlist.setToolTip(self.sentences["tips_playlist"])

        self.line_keyword = QLineEdit(self)
        self.line_keyword.setGeometry(self.width*0.25, self.height*0.55, self.width*0.3, 30)
        self.line_keyword.setEnabled(False)
        self.line_keyword.setToolTip(self.sentences["tips_line_keyword"])

        self.completer = QCompleter(self.apg.getCandidate(target="anime"), self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.popup().setStyleSheet("background-color:#3c3c3c; color:#cccccc")
        self.line_keyword.setCompleter(self.completer)
        self.logger.info("Completer was called.")

        self.label_category = QLabel(self.sentences["category"], self)
        self.label_category.setGeometry(self.width*0.1, self.height*0.47, self.width*0.2, 30)

        self.check_anime = QCheckBox(self.sentences["anime"],self)
        self.check_anime.setObjectName("anime")
        self.check_anime.toggle()
        self.check_anime.setGeometry(self.width*0.22, self.height*0.47, self.width*0.15, 30)
        self.check_anime.clicked.connect(self.checkClicked) 
        self.check_anime.setToolTip(self.sentences["tips_cat_anime"])

        self.check_game = QCheckBox(self.sentences["game"],self)
        self.check_game.setObjectName("game")
        self.check_game.toggle()
        self.check_game.setGeometry(self.width*0.33, self.height*0.47, self.width*0.15, 30)
        self.check_game.clicked.connect(self.checkClicked)
        self.check_game.setToolTip(self.sentences["tips_cat_game"])
        
        self.check_sf = QCheckBox(self.sentences["sf"],self)
        self.check_sf.setObjectName("sf")
        self.check_sf.toggle()
        self.check_sf.setGeometry(self.width*0.44, self.height*0.47, self.width*0.15, 30)
        self.check_sf.clicked.connect(self.checkClicked)
        self.check_sf.setToolTip(self.sentences["tips_cat_sf"])

        self.keyword = QCheckBox(self.sentences["anime_title"],self)
        self.keyword.setObjectName("keyword")
        self.keyword.setGeometry(self.width*0.10, self.height*0.55, self.width*0.15, 30)
        self.keyword.clicked.connect(self.checkClicked)
        self.keyword.setToolTip(self.sentences["tips_keyword"])

        # Define the push button for start the process
        self.run = QPushButton(self.sentences["run"], self)
        self.run.setObjectName('run')

        self.run.setGeometry(self.width*0.35, self.height*0.85, self.width*0.15, 30)
        self.run.clicked.connect(self.buttonClicked) 
        self.run.setEnabled(True)
        self.run.setToolTip(self.sentences["tips_run"])

        # Define the push button for making the database
        self.db_update = QPushButton(self.sentences["db_update"], self)
        self.db_update.setObjectName('db_update')
    
        self.db_update.setGeometry(self.width*0.75, self.height*0.65, self.width*0.15, 30)
        self.db_update.clicked.connect(self.buttonClicked) 
        self.db_update.setEnabled(True)
        self.db_update.setToolTip(self.sentences["tips_database"])

        # Define the push button for stop the process
        self.stop = QPushButton(self.sentences["stop"], self)
        self.stop.setObjectName('stop')

        self.stop.setGeometry(self.width*0.55, self.height*0.85, self.width*0.15, 30)
        self.stop.clicked.connect(self.buttonClicked) 
        self.stop.setEnabled(False)
        self.stop.setToolTip(self.sentences["tips_stop"])
        
        # Define the progress bar
        self.progress = QProgressBar(self)
        self.progress.setGeometry(self.width*0.55, self.height*0.95, self.width*0.4, 20)
        self.progress.setMaximum(100)
        
        # Define the status bar
        self.status = QStatusBar(self)
        self.status.setGeometry(self.width*0.01, self.height*0.95, self.width*0.5, 20)
        self.status.showMessage(self.sentences["init"])
        
        self.setWindowTitle('Anison Playlist Generator')
        self.setWindowTitle

        self.thread_prog = SubProgress()
        self.thread_prog.signal.connect(self.updateProgress)

        self.thread_updateDB = None
        self.thread_genPlaylist = None
        
    def __del__(self):
        self.config.saveConfig(
            name=self.path_config, path_library=self.path_to_library, path_data=self.path_to_data, 
            path_playlist=self.path_to_playlist, path_database=self.path_to_database, width=800, height=480,
            path_style="./styles/style.qss", language=self.language
        )

    def paintEvent(self, event):
        self.painter = QPainter(self)
        self.painter.setBrush(QColor(30,30,30))
        self.painter.setPen(QColor(160,160,160))
        rect = QRect(int(self.width*0.05),int(self.height*0.43), int(self.width*0.90), int(self.height*0.40))
        self.painter.drawRoundedRect(rect, 20.0, 20.0)
        self.painter.end()

    def updateText(self, var, folder=True, ext=".m3u"):
        updated_path = ""

        if folder:
            updated_path = QFileDialog.getExistingDirectory(None, 'rootpath', var.text())
        else:
            updated_path = QFileDialog.getOpenFileName(None, 'rootpath', var.text())[0]

        if updated_path == "" or (os.path.isfile(updated_path) and os.path.splitext(updated_path)[1] != ext):
            var.setText(var.text())
        else:
            var.setText(updated_path)

        return updated_path

    def checkClicked(self):
        sender = self.sender()
        if sender.objectName() == "keyword":
            if self.keyword.checkState():
                self.status.showMessage(sender.text().replace(":", "") + self.sentences["enable"])
                self.line_keyword.setEnabled(True)
            else:
                self.status.showMessage(sender.text().replace(":", "") + self.sentences["disable"])
                self.line_keyword.setEnabled(False)

        elif sender.objectName() == "anime":
            if self.check_anime.checkState():
                self.status.showMessage(self.check_anime.text() + self.sentences["enable"])
            else:
                self.status.showMessage(self.check_anime.text() + self.sentences["disable"])

        elif sender.objectName() == "game":
            if self.check_game.checkState():
                self.status.showMessage(self.check_game.text() + self.sentences["enable"])
            else:
                self.status.showMessage(self.check_game.text() + self.sentences["disable"])

        elif sender.objectName() == "sf":
            if self.check_sf.checkState():
                self.status.showMessage(self.check_sf.text() + self.sentences["enable"])
            else:
                self.status.showMessage(self.check_sf.text() + self.sentences["disable"])

    def buttonClicked(self):
        sender = self.sender()
        self.status.showMessage(sender.text() + self.sentences["pressed"])

        if sender.objectName() == "path_data":
            self.path_to_data = self.updateText(self.line_data)
            
        elif sender.objectName() == "path_library":
            self.path_to_library = self.updateText(self.line_library)

        elif sender.objectName() == "path_playlist":
            self.path_to_playlist = self.updateText(self.line_playlist, False, ".m3u")

        elif sender.objectName() == "run":
            self.logger.info("Started to making the playlist.")

            # 既に実行しているスレッドがある場合は処理を中止            
            if self.checkThreadRunning():
                self.logger.info("GenPlaylist: The previous thread is running.")
                QMessageBox.warning(None, self.sentences["warn_overwrite"] , "直前の処理を中断しています．", QMessageBox.Ok)
                return
            
            # ファイルの拡張子の確認
            if os.path.splitext(self.line_playlist.text())[1] != ".m3u":
                self.status.showMessage(self.sentences["warn_ext"])
                return

            # プレイリストが存在するか確認
            if os.path.exists(self.line_playlist.text()):
                react = QMessageBox.warning(None, self.sentences["warn_overwrite"] , self.sentences["message_overwrite"], QMessageBox.Yes, QMessageBox.No)

                if react == QMessageBox.No:
                    self.lockInput(enabled=True)
                    return

            # チェックボックスの状態の確認
            check_categories = {"anison":self.check_anime.checkState(), "game":self.check_game.checkState(), "sf":self.check_sf.checkState()}

            # プレイリスト作成用のスレッドの呼び出し
            self.thread_genPlaylist = GenPlaylist(
                                apg=self.apg,
                                keyword=self.line_keyword.text() if self.keyword.checkState() else "",
                                use_key=1 if self.keyword.checkState() else 0,
                                path_playlist=self.line_playlist.text(),
                                check_categories=check_categories)
            self.thread_genPlaylist.signal.connect(self.generatePlaylist)

            # マルチスレッドによる処理の開始
            self.lockInput(enabled=False)
            self.thread_prog.start()
            self.thread_genPlaylist.start()

        elif sender.objectName() == "db_update":
            self.logger.info("Started to updating the database.")

            # 既に実行しているスレッドがある場合は処理を中止 
            if self.checkThreadRunning():
                self.logger.info("UpdateDB: The previous thread is running.")
                QMessageBox.warning(None, self.sentences["warn_overwrite"] , "直前の処理を中断中です", QMessageBox.Ok)
                return
            
            # データベース更新処理の確認
            react = QMessageBox.warning(None, self.sentences["warn_overwrite"] , "データベースを更新しますか?", QMessageBox.Yes, QMessageBox.No)

            # Noなら処理を中止
            if react == QMessageBox.No:
                self.lockInput(enabled=True)
                return
            
            # スレッドの実行準備
            self.thread_updateDB = UpdateDB(apg=self.apg, path_data=self.line_data.text(), path_library=self.line_library.text())
            self.thread_updateDB.signal.connect(self.updateDB)
            
            # ボタンなどの入力が出来ないようにする
            self.lockInput(enabled=False)
            
            # マルチスレッドによる処理の開始
            self.thread_prog.start()
            self.thread_updateDB.start()

        elif sender.objectName() == "stop":
            self.apg.stop()
            self.apg.reset()

            self.thread_prog.wait()
            self.thread_prog.quit()
            
            if self.thread_updateDB != None:                  
                self.thread_updateDB.wait()
                self.thread_updateDB.quit()

            elif self.thread_genPlaylist != None:
                self.thread_genPlaylist.wait()
                self.thread_genPlaylist.quit()
                
            self.status.showMessage(self.sentences["warn_stop"])
            self.lockInput(enabled=True)
    
    def checkThreadRunning(self):
        """
        マルチスレッド処理が行われているかを返す関数
        """
        check_updateDB = (self.thread_updateDB != None) and self.thread_updateDB.isRunning()
        check_genPlaylist = (self.thread_genPlaylist != None) and self.thread_genPlaylist.isRunning()
        
        return check_updateDB or check_genPlaylist

    def lockInput(self, enabled=True):
        """
        ボタン入力などの有効/無効を切り替える関数
        """

        self.stop.setEnabled(not enabled)
        self.run.setEnabled(enabled)
        self.db_update.setEnabled(enabled)

        self.check_anime.setEnabled(enabled)
        self.check_game.setEnabled(enabled)
        self.check_sf.setEnabled(enabled)
        self.keyword.setEnabled(enabled)
        self.line_keyword.setEnabled(enabled)

        self.button_data.setEnabled(enabled)
        self.button_library.setEnabled(enabled)
        self.button_playlist.setEnabled(enabled)

        self.line_data.setEnabled(enabled)
        self.line_playlist.setEnabled(enabled)
        self.line_library.setEnabled(enabled)
        
        return 

    def updateProgress(self, signal):
        """
        プログレスバーの値を更新する関数
        """
        db, library, playlist = self.apg.getProgress()
        value = 0

        if 0 < playlist and playlist < 100:
            value = playlist
        elif 0 < db and db < 100:
            value = db
        else:
            value = library
        
        self.progress.setValue(value)

    def resetProgress(self):
        """
        ProgressBarの値を0にする関数
        """
        self.progress.setValue(0)

    def generatePlaylist(self, signal):
        """
        GenPlaylistスレッド実行時に呼び出される関数
        空白を受信したらスレッドを終了する
        """
        if signal != "":
            self.status.showMessage(signal)
        else:
            self.apg.reset()

            self.thread_genPlaylist.wait()
            self.thread_genPlaylist.quit()

            self.thread_prog.wait()
            self.thread_prog.quit()

            self.resetProgress()
            self.lockInput(enabled=True)

            # メッセージの表示
            self.status.showMessage(self.sentences["fin_making_playlist"])

    def updateDB(self, signal):
        """
        UpdateDBスレッド実行時に呼び出される関数
        空白を受信したらスレッドを終了する
        """
        if signal != "":
            self.status.showMessage(signal)
        else:
            self.apg.reset()

            self.thread_updateDB.wait()
            self.thread_updateDB.quit()
            self.thread_prog.wait()
            self.thread_prog.quit()

            self.resetProgress()
            self.lockInput(enabled=True)
            
            # 検索候補の更新
            self.completer.model().setStringList(self.apg.getCandidate(target="anime"))
            
            # メッセージの表示
            self.status.showMessage(self.sentences["fin_updating_database"])


def run(path_config='./config.ini', path_style='./styles/style.qss', logger=None):
    try:
        app = QApplication(sys.argv)
        main_window = MainWindow(path_config=path_config, path_style=path_style, logger=logger)
        main_window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(e)

if __name__ == '__main__':
    run(path_config='./config.ini', path_style='./styles/style.qss')
