import os
import sys
import threading
import time

from PyQt5.QtCore import QRect, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import (QApplication, QCheckBox, QFileDialog, QLabel,
                             QLineEdit, QProgressBar, QPushButton, QSpinBox,
                             QStatusBar, QWidget, QMessageBox)

from .apg import APG
from .config import Config
from .sentence import LANG_ENG, LANG_JA


class SubProgress(QThread):
    signal = pyqtSignal(int)
    running = True

    def run(self):
        self.running=True
        while self.running:
            time.sleep(0.01)
            self.signal.emit(0)

    def wait(self):
        self.running = False


class MainWindow(QWidget):
    def __init__(self, parent=None, path_config='config.ini', path_style='./styles/style.qss'):
        super(MainWindow, self).__init__(parent)
        self.path_config = path_config
        self.config = Config(self.path_config)
        self.settings = self.config.getConfig()
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

        self.apg = APG(self.path_to_database)
        
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
        # self.keyword.setToolTip("")

        self.generate_only = QCheckBox(self.sentences["gen_playlist_only"],self)
        self.generate_only.setObjectName("gen")
        self.generate_only.toggle()
        self.generate_only.setGeometry(self.width*0.10, self.height*0.64, self.width*0.4, 30)
        self.generate_only.clicked.connect(self.checkClicked)
        self.generate_only.setToolTip(self.sentences["tips_gen_only"])

        # Define the push button for start the process
        self.run = QPushButton(self.sentences["run"], self)
        self.run.setObjectName('run')

        self.run.setGeometry(self.width*0.35, self.height*0.85, self.width*0.15, 30)
        self.run.clicked.connect(self.buttonClicked) 
        self.run.setEnabled(True)
        self.run.setToolTip(self.sentences["tips_run"])

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
        self.stop_thread = threading.Event()

        self.thread_prog = SubProgress()
        self.thread_prog.signal.connect(self.updateProgress)
    
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

        elif sender.objectName() == "gen":
            if self.generate_only.checkState():
                self.status.showMessage(self.generate_only.text() + self.sentences["enable"])
            else:
                self.status.showMessage(self.generate_only.text() + self.sentences["disable"])
        
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
            if not os.path.exists(self.path_to_database) and self.generate_only.checkState():
                self.status.showMessage(self.sentences["warn_gen_playlist"])
            else:
                self.thread = threading.Thread(target=self.runAll)

                if os.path.splitext(self.line_playlist.text())[1] != ".m3u":
                    self.status.showMessage(self.sentences["warn_ext"])
                    self.lockInput(state=True)
                    return 
                
                if os.path.exists(self.line_playlist.text()):
                    react = QMessageBox.warning(None, self.sentences["warn_overwrite"] , self.sentences["message_overwrite"], QMessageBox.Yes, QMessageBox.No)

                    if react == QMessageBox.No:
                        self.lockInput(state=True)
                        return

                self.thread.setDaemon(True)
                self.thread.start()
                
                self.lockInput(state=False)
                self.stop.setEnabled(True)
                self.run.setEnabled(False)

        elif sender.objectName() == "stop":
            self.lockInput(state=True)
            self.stop.setEnabled(False)
            self.run.setEnabled(True) 
            self.apg.stop()

            self.thread.join()

            self.thread_prog.wait()
            self.thread_prog.quit()
            self.status.showMessage(self.sentences["warn_stop"])
            self.apg.reset()

    
    def lockInput(self, state=True):
        
        self.check_anime.setEnabled(state)
        self.check_game.setEnabled(state)
        self.check_sf.setEnabled(state)
        self.generate_only.setEnabled(state)
        self.keyword.setEnabled(state)
        self.line_keyword.setEnabled(state)

        self.button_data.setEnabled(state)
        self.button_library.setEnabled(state)
        self.button_playlist.setEnabled(state)

        self.line_data.setEnabled(state)
        self.line_playlist.setEnabled(state)
        self.line_library.setEnabled(state)
        
        return 

    def updateProgress(self, signal):

        db, library, playlist = self.apg.getProgress()
        value = 0

        if 0 < playlist and playlist < 100:
            value = playlist
        elif 0 < db and db < 100:
            value = db
        else:
            value = library
        
        self.progress.setValue(value)


    def runAll(self):
        self.thread_prog.start()
        
        if not self.generate_only.checkState():
            self.status.showMessage(self.sentences["make_anison"])
            self.apg.makeAnisonDatabase(self.line_data.text())

            self.status.showMessage(self.sentences["make_library"])
            self.apg.makeLibrary(self.line_library.text())

            if os.path.exists('artist_list.txt'):
                self.apg.outputArtist()

        self.status.showMessage(self.sentences["make_playlist"])
        check_category = {"anison":self.check_anime.checkState(), "game":self.check_game.checkState(), "sf":self.check_sf.checkState()}

        self.apg.generatePlaylist(self.line_playlist.text(), 
                                1 if self.keyword.checkState() else 0, 
                                self.line_keyword.text() if self.keyword.checkState() else "", 
                                check_category)

        self.status.showMessage(self.sentences["make_fin"])
        self.stop.setEnabled(False)
        self.run.setEnabled(True) 
        self.lockInput(state=True)
        self.apg.reset()
        self.thread_prog.wait()
        self.thread_prog.quit()


def run(path_config='./config.ini', path_style='./styles/style.qss'):
    app = QApplication(sys.argv)
    main_window = MainWindow(path_config=path_config, path_style=path_style)
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    run(path_config='./config.ini', path_style='./styles/style.qss')
