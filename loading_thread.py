from PyQt5.QtCore import QThread, pyqtSignal

from mysqlite import SQLiteManager


class LoadingPlaylistThread(QThread):
    """加载歌单数据的后台线程"""
    data_loaded = pyqtSignal(list)  # 发射加载的数据

    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path

    def run(self):
        """在后台执行数据库查询"""
        try:
            sqlite_manager = SQLiteManager(self.db_path)
            # 查询数据库中的所有数据，按照id排序
            data = sqlite_manager.select_all(
                'tb_collect_playlist', 
                condition="", 
                params=None,
                order_by='id'
            )
            self.data_loaded.emit(data)
        except Exception as e:
            self.logger.error(f"加载歌单数据失败: {e}")
            self.data_loaded.emit([])  # 发送空列表表示加载失败
