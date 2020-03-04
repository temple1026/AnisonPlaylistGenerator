import configparser
import glob
import os


class Config():
    def __init__(self, config_name):
        super(Config, self).__init__()
        self.config_name = config_name
        self.init()
        

    def init(self):
        inilist = glob.glob("*.ini")
        
        if not os.path.isdir("./playlist"):
            os.mkdir("./playlist")
        
        if not os.path.isdir("./data"):
            os.mkdir("./data")

        if len(inilist) == 0:
            self.saveConfig(self.config_name)
        else:
            self.config = configparser.ConfigParser()
            self.config.read(self.config_name)
    
    
    def getConfig(self):
        return self.config

    
    def checkConfig(self):
        """
        items = self.config.items('dir')

        for item in items:
            print(item)
        """
        # For validation of the ini file
        return True

    def saveConfig(self, name='config.ini', path_library='C://Users/'+os.getlogin() + '/Music', path_data='./data', 
            path_playlist='./playlist/AnimeSongs.m3u', path_database='./info.db', width=800, height=480, 
            path_style="./styles/style.qss", language="ja"):

        config = configparser.ConfigParser()

        config.add_section('path')
        config.set('path', 'library', path_library)
        config.set('path', 'data', path_data)
        config.set('path', 'playlist', path_playlist)
        config.set('path', 'database', path_database)
        
        config.add_section('screen')
        config.set('screen', 'width', str(width))
        config.set('screen', 'height', str(height))

        config.add_section('general')
        config.set('general', 'style', path_style)
        config.set('general', 'language', language)
        
        with open(name, 'w') as file:
            config.write(file)

        self.config = config

        return config
