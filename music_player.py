import os
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl

class MusicPlayer:
    def __init__(self):
        self.player = QMediaPlayer()
        # 连接播放状态信号
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)
        self.player.mediaStatusChanged.connect(self.status_changed)
        
        self.current_file = None

    def load_file(self, file_path):
        """加载音频文件"""
        try:
            # 直接使用URL方式
            url = QUrl.fromLocalFile(file_path)
            self.player.setMedia(QMediaContent(url))
            self.current_file = file_path
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def play(self, file_path=None):
        """播放音频 - 支持指定文件播放或继续播放当前文件"""
        if file_path:
            # 如果指定了文件路径，则加载并播放
            if self.load_file(file_path):
                self.player.play()
                return True
            else:
                return False
        else:
            # 如果没有指定文件路径
            if self.is_playing():
                # 如果正在播放，则暂停
                self.player.pause()
            elif self.current_file and os.path.exists(self.current_file):
                # 如果有当前文件且文件存在，则继续播放
                self.player.play()
                return True
            else:
                # 如果没有当前播放文件，则返回False，让调用方处理默认播放
                return False
    
    def pause(self):
        """暂停播放"""
        self.player.pause()
    
    def stop(self):
        """停止播放"""
        self.player.stop()
    
    def set_volume(self, volume):
        """设置音量 (0-100)"""
        self.player.setVolume(volume)
    
    def set_position(self, position):
        """设置播放位置（毫秒）"""
        self.player.setPosition(position)
    
    def get_position(self):
        """获取当前播放位置"""
        return self.player.position()
    
    def get_duration(self):
        """获取总时长"""
        return self.player.duration()
    
    def is_playing(self):
        """检查是否正在播放"""
        return self.player.state() == QMediaPlayer().PlayingState
    
    # 回调函数
    def position_changed(self, position):
        # 播放进度变化时调用
        pass
    
    def duration_changed(self, duration):
        # 音频总时长变化时调用
        pass
    
    def status_changed(self, status):
        # 媒体状态变化时调用
        pass
