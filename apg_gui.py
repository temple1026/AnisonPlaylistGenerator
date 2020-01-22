import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import *
import sip
import os
import threading

from apg import APG
from config import Config
import time


class SubProgress(QThread):
    signal = pyqtSignal(int)
    run = True

    def run(self):
        self.run=True
        while self.run:
            time.sleep(0.01)
            self.signal.emit(0)

    def wait(self):
        self.run = False

class MainWindow(QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.config = Config('config.ini')
        self.settings = self.config.getConfig()
        
        style = '''
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

        self.setStyleSheet(style)

        self.path_to_data = self.settings.get('path', 'data')
        self.path_to_library = self.settings.get('path', 'library')
        self.path_to_playlist = self.settings.get('path', 'playlist')
        self.path_to_database = self.settings.get('path', 'database')

        self.apg = APG(self.path_to_database)
        
        self.width = int(self.settings.get('screen', 'width'))
        self.height = int(self.settings.get('screen', 'height'))
        
        self.label_data = QLabel('Path to data :', self)
        self.label_data.setGeometry(self.width*0.08, self.height*0.10, self.width*0.2, 30)

        self.label_library = QLabel(' Path to library :', self)
        self.label_library.setGeometry(self.width*0.08, self.height*0.20, self.width*0.2, 30)

        self.label_playlist = QLabel('Path to playlist :', self)
        self.label_playlist.setGeometry(self.width*0.08, self.height*0.30, self.width*0.2, 30)

        self.label_advanced = QLabel('  Advanced Settings  ', self)
        self.label_advanced.setGeometry(self.width*0.1, self.height*0.40, self.width*0.21, 30)

        self.setFixedSize(self.width, self.height)

        self.button_data = QPushButton('Select', self)
        self.button_data.setObjectName('path_data')
        self.button_data.setGeometry(self.width*0.78, self.height*0.10, self.width*0.15, 30)
        self.button_data.clicked.connect(self.buttonClicked) 

        self.button_library = QPushButton('Select', self)
        self.button_library.setObjectName('path_library')
        self.button_library.setGeometry(self.width*0.78, self.height*0.20, self.width*0.15, 30)
        self.button_library.clicked.connect(self.buttonClicked) 

        self.button_playlist = QPushButton('Select', self)
        self.button_playlist.setObjectName('path_playlist')
        self.button_playlist.setGeometry(self.width*0.78, self.height*0.30, self.width*0.15, 30)
        self.button_playlist.clicked.connect(self.buttonClicked) 

        self.line_data = QLineEdit(self.path_to_data, self)
        self.line_data.setGeometry(self.width*0.27, self.height*0.10, self.width*0.5, 30)

        self.line_library = QLineEdit(self.path_to_library, self)
        self.line_library.setGeometry(self.width*0.27, self.height*0.20, self.width*0.5, 30)
        
        self.line_playlist = QLineEdit(self.path_to_playlist, self)
        self.line_playlist.setGeometry(self.width*0.27, self.height*0.30, self.width*0.5, 30)

        self.line_keyword = QLineEdit(self)
        self.line_keyword.setGeometry(self.width*0.30, self.height*0.55, self.width*0.3, 30)
        self.line_keyword.setEnabled(False)

        self.label_category = QLabel('Categories :', self)
        self.label_category.setGeometry(self.width*0.1, self.height*0.47, self.width*0.2, 30)

        self.check_anime = QCheckBox('Anime',self)
        self.check_anime.setObjectName("anime")
        self.check_anime.toggle()
        self.check_anime.setGeometry(self.width*0.23, self.height*0.47, self.width*0.1, 30)
        self.check_anime.clicked.connect(self.checkClicked) 

        self.check_game = QCheckBox('Game',self)
        self.check_game.setObjectName("game")
        self.check_game.toggle()
        self.check_game.setGeometry(self.width*0.35, self.height*0.47, self.width*0.1, 30)
        self.check_game.clicked.connect(self.checkClicked) 
        
        self.check_sf = QCheckBox('SF',self)
        self.check_sf.setObjectName("sf")
        self.check_sf.toggle()
        self.check_sf.setGeometry(self.width*0.47, self.height*0.47, self.width*0.1, 30)
        self.check_sf.clicked.connect(self.checkClicked) 

        self.keyword = QCheckBox('Use anime title :',self)
        self.keyword.setObjectName("keyword")
        self.keyword.setGeometry(self.width*0.10, self.height*0.55, self.width*0.2, 30)
        self.keyword.clicked.connect(self.checkClicked)

        self.generate_only = QCheckBox('Generate playlist only',self)
        self.generate_only.setObjectName("gen")
        self.generate_only.toggle()
        self.generate_only.setGeometry(self.width*0.10, self.height*0.64, self.width*0.3, 30)
        self.generate_only.clicked.connect(self.checkClicked)

        self.duplication = QCheckBox('Allow duplication',self)
        self.duplication.setObjectName("dup")
        self.duplication.toggle()
        self.duplication.setGeometry(self.width*0.10, self.height*0.74, self.width*0.3, 30)
        self.duplication.clicked.connect(self.checkClicked) 

        # Define the spin button for the similarity of title
        self.label_spin_title = QLabel(' Rate of title :', self)
        self.label_spin_title.setGeometry(self.width*0.63, self.height*0.55, self.width*0.15, 30)

        self.spin_title = QSpinBox(self)
        self.spin_title.setRange(0, 100)
        self.spin_title.setValue(55)
        self.spin_title.setGeometry(self.width*0.8, self.height*0.55, self.width*0.1, 30)
        
        # Define the spin button for the similality of artist
        self.label_spin_artist = QLabel('Rate of artist :', self)
        self.label_spin_artist.setGeometry(self.width*0.63, self.height*0.65, self.width*0.15, 30)

        self.spin_artist = QSpinBox(self)
        self.spin_artist.setRange(0, 100)
        self.spin_artist.setValue(80)
        self.spin_artist.setGeometry(self.width*0.8, self.height*0.65, self.width*0.1, 30)

        # Define the push button for start the process
        self.run = QPushButton('Run', self)
        self.run.setObjectName('run')

        self.run.setGeometry(self.width*0.35, self.height*0.85, self.width*0.15, 30)
        self.run.clicked.connect(self.buttonClicked) 
        self.run.setEnabled(True)

        # Define the push button for stop the process
        self.stop = QPushButton('Stop', self)
        self.stop.setObjectName('stop')

        self.stop.setGeometry(self.width*0.55, self.height*0.85, self.width*0.15, 30)
        self.stop.clicked.connect(self.buttonClicked) 
        self.stop.setEnabled(False)
        
        # Define the progress bar
        self.progress = QProgressBar(self)
        self.progress.setGeometry(self.width*0.55, self.height*0.95, self.width*0.4, 20)
        self.progress.setMaximum(100)
        
        # Define the status bar
        self.status = QStatusBar(self)
        self.status.setGeometry(self.width*0.01, self.height*0.95, self.width*0.5, 20)
        self.status.showMessage('Welcome to Anison Playlist Generator.')
        
        self.setWindowTitle('Anison Playlist Generator')

        self.stop_thread = threading.Event()

        self.thread_prog = SubProgress()
        self.thread_prog.signal.connect(self.updateProgress)
    
    def __del__(self):
        self.config.saveConfig(
            name='config.ini', path_library=self.line_library.text(), path_data=self.line_data.text(), 
            path_playlist=self.line_playlist.text(), path_database=self.path_to_database, width=640, height=480
        )

    def paintEvent(self, event):
        self.painter = QPainter(self)
        # self.painter.drawRect(int(self.width*0.01), int(self.height*0.6), int(self.width*0.98), int(self.height*0.4))
        self.painter.setBrush(QColor(240,248,255))
        self.painter.setPen(QColor(160,160,160))
        rect = QRect(int(self.width*0.05),int(self.height*0.43), int(self.width*0.90), int(self.height*0.40))
        self.painter.drawRoundedRect(rect, 20.0, 20.0)
        self.painter.end()

    def updateText(self, var, folder=True, ext=".m3u"):
        if folder:
            path = QFileDialog.getExistingDirectory(None, 'rootpath', var.text())
        else:
            path = QFileDialog.getOpenFileName(None, 'rootpath', var.text())
            path = path[0]
            
        if path == "" or (os.path.isfile(path) and os.path.splitext(path)[1] != ext):
            var.setText(var.text())
        else:
            var.setText(path)
       

    def checkClicked(self):
        sender = self.sender()
        if sender.objectName() == "keyword":
            if self.keyword.checkState():
                self.status.showMessage(sender.text().replace(":", "") + ' was enabled.')
                self.line_keyword.setEnabled(True)
            else:
                self.status.showMessage(sender.text().replace(":", "") + ' was disabled.')
                self.line_keyword.setEnabled(False)
        elif sender.objectName() == "gen":
            if self.generate_only.checkState():
                self.status.showMessage(self.generate_only.text() + ' was enabled')
            else:
                self.status.showMessage(self.generate_only.text() + ' was disabled')
        elif sender.objectName() == "dup":
            if self.duplication.checkState():
                self.status.showMessage(self.duplication.text() + ' was enabled.')
            else:
                self.status.showMessage(self.duplication.text() + ' was disabled.')

    def buttonClicked(self):
        sender = self.sender()
        self.status.showMessage(sender.text() + ' was pressed.')
        
        if sender.objectName() == "path_data":
            self.updateText(self.line_data)

        elif sender.objectName() == "path_library":
            self.updateText(self.line_library)

        elif sender.objectName() == "path_playlist":
            self.updateText(self.line_playlist, False, ".m3u")
            
        elif sender.objectName() == "run":
            if not os.path.exists(self.path_to_database) and self.generate_only.checkState():
                self.status.showMessage('You must run without "Generate playlist only"')
            else:
                self.thread = threading.Thread(target=self.runAll)
                self.thread.setDaemon(True)
                self.thread.start()
                
                self.stop.setEnabled(True)
                self.run.setEnabled(False)

        elif sender.objectName() == "stop":
            self.stop.setEnabled(False)
            self.run.setEnabled(True) 
            self.apg.stop()

            self.thread.join()

            self.thread_prog.wait()
            self.thread_prog.quit()
            self.status.showMessage("Process interrupted.")
            self.apg.reset()


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
        
        if os.path.splitext(self.line_playlist.text())[1] != ".m3u":
            self.status.showMessage("Extension of the path to playlist must be .m3u.")
        else:

            self.thread_prog.start()
            
            if not self.generate_only.checkState():
                self.status.showMessage('Making Anison Database.')
                self.apg.makeAnisonDatabase(self.line_data.text())

                self.status.showMessage('Making library Library.')
                self.apg.makeLibrary(self.line_library.text())

                if os.path.exists('artist_list.txt'):
                    self.apg.outputArtist()

            self.status.showMessage('Making Playlist.')
            check_category = {"anison":self.check_anime.checkState(), "game":self.check_game.checkState(), "sf":self.check_sf.checkState()}

            self.apg.generatePlaylist(self.line_playlist.text(), 
                                    self.keyword.checkState(), 
                                    self.line_keyword.text(), 
                                    float(self.spin_title.text())/100, 
                                    float(self.spin_artist.text())/100,
                                    self.duplication.checkState(),
                                    check_category)

            self.status.showMessage('A playlist was generated')
            self.stop.setEnabled(False)
            self.run.setEnabled(True) 
            
            self.apg.reset()
            self.thread_prog.wait()
            self.thread_prog.quit()


def run():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    run()


