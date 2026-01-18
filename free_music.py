#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author: unknown
@Date: 2026-01-18
@File: free_music.py
"""
import re
import sys
import os

import requests
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox

from PyQt5 import QtCore, QtGui, QtWidgets

from freemain import Ui_Dialog
from get_music import get_music
from loading_thread import LoadingPlaylistThread
from music_player import MusicPlayer
from mysqlite import SQLiteManager
from utils import download_image, is_binary_file
from log_handle import app_logger  # 导入日志配置


class ImageDownloadThread(QThread):
    """
    图片下载线程
    """
    download_finished = pyqtSignal(int, str)  # 发射信号，包含行号和图片路径

    def __init__(self, url, row, parent=None):
        super().__init__(parent)
        self.url = url
        self.row = row
        self.logger = app_logger  # 使用全局logger

    def run(self):
        try:
            image_name = re.findall(r"==/(.*?\.jpg)\?", self.url, re.ASCII)[0]
            temp_path = os.path.join('./image', image_name)
            download_image(self.url, temp_path)
            self.download_finished.emit(self.row, temp_path)
            self.logger.info(f"图片下载成功: {temp_path}")
        except Exception as e:
            self.logger.error(f"下载图片失败: {e}, URL: {self.url}")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = app_logger  # 使用全局logger

        # 创建UI实例
        self.ui = Ui_Dialog()
        # 设置UI到当前窗口
        self.ui.setupUi(self)  # 将当前窗口作为参数传入setupUi
        # 可以重写窗口标题
        self.setWindowTitle("Free Music Player")

        # 初始化音乐播放器
        self.music_player = MusicPlayer()
        self.current_play_row = None
        # 收藏歌单
        self.collect_list = []
        self.current_song_list = []

        self.page = 1
        self.image_dir = "./image"
        self.music_dir = "./songs"
        self.cache_dir = "./temp"

        self.init_mkdir()
        self.db_path = "./music.db"
        sqlite_manager = SQLiteManager(self.db_path)
        sqlite_manager.create_table('tb_collect_playlist',
                                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                                    "title VARCHAR(255), "
                                    "author VARCHAR(255), "
                                    "pic VARCHAR(255), "
                                    "wording VARCHAR(255), "
                                    "musicing VARCHAR(255), "
                                    "play_url VARCHAR(255), "
                                    "create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
                                    "active BOOLEAN DEFAULT 1"
                                    )
        self.band_event()
        self.setup_player_controls()
        self.load_collect_playlist()
        self.logger.info("MainWindow初始化完成")

    def init_mkdir(self):
        """
        创建初始需要的目录
        """
        for dir_path in [self.image_dir, self.music_dir, self.cache_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

    def band_event(self):
        # 绑定事件
        self.ui.pushButton_5.clicked.connect(self.btn_next_page)
        self.ui.pushButton_6.clicked.connect(self.btn_prev_page)
        self.ui.pushButton_7.clicked.connect(self.search_music)
        self.ui.pushButton_8.clicked.connect(self.clear_table)
        # 连接表格双击事件
        self.ui.tableWidget_2.cellDoubleClicked.connect(self.table_double_clicked)

        # 连接列表双击事件
        self.ui.listWidget.itemDoubleClicked.connect(self.list_double_clicked)

    def setup_player_controls(self):
        """设置播放器控制界面"""
        # 创建播放控制布局
        control_layout = QtWidgets.QHBoxLayout()

        # 播放/暂停按钮
        self.play_button = QtWidgets.QPushButton("播放")
        self.play_button.clicked.connect(self.toggle_play_pause)

        # 停止按钮
        self.stop_button = QtWidgets.QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_music)

        # 音量控制
        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.change_volume)

        # 进度条
        self.progress_bar = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.sliderPressed.connect(self.on_progress_press)  # 按下时
        self.progress_bar.sliderMoved.connect(self.on_progress_moving)  # 移动时
        self.progress_bar.sliderReleased.connect(self.on_progress_release)  # 释放时

        # 添加到布局
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(QtWidgets.QLabel("音量:"))
        control_layout.addWidget(self.volume_slider)
        control_layout.addWidget(QtWidgets.QLabel("进度:"))
        control_layout.addWidget(self.progress_bar)

        # 将控制布局添加到主布局
        self.ui.verticalLayout.addLayout(control_layout)

    def on_progress_press(self):
        """进度条按下事件 - 暂停自动更新"""
        self.logger.info("进度条被按下")
        # 可以在这里暂停自动进度更新
        self.is_user_seeking = True

    def on_progress_moving(self, value):
        """进度条移动事件 - 显示预览位置"""
        # 这里可以显示预览位置，但不实际跳转
        self.logger.debug(f"进度条移动到: {value}%")

    def on_progress_release(self):
        """进度条释放事件 - 获取最终坐标并跳转"""
        self.logger.info("进度条释放")
        final_value = self.progress_bar.value()
        self.logger.info(f"拖动完成，最终坐标: {final_value}%")

        # 计算实际播放位置
        if self.music_player.get_duration() > 0:
            actual_position = (final_value / 100.0) * self.music_player.get_duration()
            self.music_player.set_position(int(actual_position))
            self.logger.info(f"跳转到位置: {int(actual_position)}ms")

        self.is_user_seeking = False

    def play_music(self, row):
        """播放指定行的音乐"""
        self.logger.info(f"开始播放音乐: {row[0]} - {row[1]}")

        # 构造本地文件路径
        filename = f"{row[0]}--{row[1]}.mp3"
        filepath = os.path.join(self.cache_dir, filename)

        if os.path.exists(filepath):
            if self.music_player.load_file(filepath):
                self.music_player.play(filepath)
                self.play_button.setText("暂停")
                self.current_play_row = row
                self.logger.info(f"音乐播放开始: {filepath}")

                # 更新播放状态
                self.update_play_status()
            else:
                self.logger.error(f"无法加载音频文件: {filepath}")
                QMessageBox.warning(self, "错误", "无法加载音频文件")

    def toggle_play_pause(self):
        """切换播放/暂停 - 优先播放当前节点，否则播放收藏夹第一条"""
        if self.music_player.is_playing():
            # 如果正在播放，则暂停
            self.music_player.pause()
            self.play_button.setText("播放")
        else:
            # 如果没有正在播放，则尝试播放当前选中的行
            if self.music_player.player.state() == QMediaPlayer.PausedState:
                self.music_player.play()
            else:
                # 如果没有当前播放项，尝试播放收藏夹第一条
                if len(self.collect_list):
                    # 播放收藏夹第一条
                    self.download_music(self.collect_list[0][1:], type="cache")
                    self.play_music(self.collect_list[0][1:3])
                else:
                    # 如果没有收藏的音乐，尝试播放当前表格的第一行
                    current_row = self.ui.tableWidget_2.currentRow()
                    if current_row >= 0:
                        song_info = self.current_song_list[current_row]
                        self.download_music(song_info, type="cache")
                        self.play_music(song_info)
                    else:
                        QMessageBox.warning(self, "错误", "没有可播放的音乐")

    def stop_music(self):
        """停止播放"""
        self.music_player.stop()
        self.play_button.setText("播放")
        self.progress_bar.setValue(0)

    def change_volume(self, value):
        """改变音量"""
        self.music_player.set_volume(value)

    def update_play_status(self):
        """更新播放状态显示"""
        # 这里可以添加定时器来更新进度条
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_progress)
        timer.start(1000)  # 每秒更新一次

    def update_progress(self):
        """更新播放进度"""
        if self.music_player.get_duration() > 0:
            position = self.music_player.get_position()
            duration = self.music_player.get_duration()
            progress = int((position / duration) * 100)
            self.progress_bar.setValue(progress)

    def table_double_clicked(self, row):
        """
        表格双击事件处理
        :param row: 行索引
        """
        self.logger.info(f"双击表格第 {row} 行")
        # 从内部存储的歌曲信息中获取完整数据
        if 0 <= row < len(self.current_song_list):
            song_info = self.current_song_list[row]
            filename = f"{song_info[0]}--{song_info[1]}.mp3"
            filepath = os.path.join(self.cache_dir, filename)
            if not os.path.exists(filepath):
                self.logger.warning(f"收藏的音乐文件不存在: {filepath}")
                self.download_music(song_info, type="cache")
            self.play_music(song_info)

    def list_double_clicked(self, item):
        """
        列表双击事件处理
        :param item: 被点击的列表项
        """
        self.logger.info(f"双击列表项: {item.text()}")

        # 从自定义角色中获取完整的歌曲信息
        full_data = item.data(QtCore.Qt.UserRole)
        self.logger.debug(f"获取的完整歌曲信息: {full_data}")

        if full_data:
            # 从存储的数据中获取完整信息
            title = full_data[1]
            author = full_data[2]
            play_url = full_data[6]

            # 构造本地文件路径
            filename = f"{title}--{author}.mp3"
            filepath = os.path.join(self.cache_dir, filename)
            song_info = [title, author, "", "", "", play_url]

            if not os.path.exists(filepath):
                self.logger.warning(f"收藏的音乐文件不存在: {filepath}")
                self.download_music(song_info, type="cache")
            self.play_music(song_info)

    def on_image_downloaded(self, row, image_path):
        """
        图片下载完成回调
        """
        try:
            import os
            pixmap = QtGui.QPixmap(image_path)
            if not pixmap.isNull():
                image_label = QtWidgets.QLabel()
                scaled_pixmap = pixmap.scaled(
                    25, 25,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation
                )
                image_label.setPixmap(scaled_pixmap)
                image_label.setAlignment(QtCore.Qt.AlignCenter)
                image_label.setMaximumSize(25, 25)
                self.ui.tableWidget_2.setCellWidget(row, 3, image_label)
            self.logger.debug(f"图片显示成功: {image_path}")
        except Exception as e:
            self.logger.error(f"处理下载的图片失败: {e}, Path: {image_path}")

    def search_music(self):
        song_name = self.ui.lineEdit_2.text()
        self.logger.info(f"开始搜索音乐: {song_name}, 页码: {self.page}")

        try:
            ret, song_info = get_music(song_name, self.page)
            if ret:
                # 存储当前歌曲列表，用于双击事件
                self.current_song_list = song_info

                # 清空现有数据
                self.ui.tableWidget_2.setRowCount(0)

                # 存储下载线程
                self.image_threads = []

                for row_index, item in enumerate(song_info):
                    [title, author, pic, wording, musicing, play_url] = item
                    title = re.sub(r'[^\w\s\u4e00-\u9fff]', '', title)
                    author = re.sub(r'[^\w\s\u4e00-\u9fff]', '', author)
                    item[0] = title
                    item[1] = author

                    self.ui.tableWidget_2.setRowCount(row_index + 1)
                    # 逐列设置数据
                    self.ui.tableWidget_2.setItem(row_index, 1, QtWidgets.QTableWidgetItem(title))
                    self.ui.tableWidget_2.setItem(row_index, 2, QtWidgets.QTableWidgetItem(author))

                    # 创建占位标签
                    placeholder_label = QtWidgets.QLabel("加载中...")
                    placeholder_label.setAlignment(QtCore.Qt.AlignCenter)
                    placeholder_label.setMaximumSize(25, 25)
                    self.ui.tableWidget_2.setCellWidget(row_index, 3, placeholder_label)

                    thread = ImageDownloadThread(pic, row_index)
                    thread.download_finished.connect(self.on_image_downloaded)
                    self.image_threads.append(thread)
                    thread.start()

                    self.ui.tableWidget_2.setItem(row_index, 4, QtWidgets.QTableWidgetItem(wording))
                    self.ui.tableWidget_2.setItem(row_index, 5, QtWidgets.QTableWidgetItem(musicing))

                    # 第1列（操作列）添加图标按钮
                    btn_widget = QtWidgets.QWidget()
                    layout = QtWidgets.QHBoxLayout(btn_widget)
                    layout.setContentsMargins(2, 2, 2, 2)
                    layout.setSpacing(2)

                    # 下载按钮
                    download_btn = QtWidgets.QToolButton()
                    download_btn.setIcon(QtGui.QIcon("./icons/download.png"))
                    download_btn.setToolTip("下载当前行歌曲")
                    download_btn.clicked.connect(lambda checked=False, item_copy=item: self.download_music(item_copy))

                    # 收藏按钮
                    collect_btn = QtWidgets.QToolButton()
                    collect_btn.setIcon(QtGui.QIcon("./icons/add.png"))
                    collect_btn.setToolTip("添加到个人收藏夹")
                    collect_btn.clicked.connect(lambda checked=False, item_copy=item: self.collect_playlist(item_copy))

                    # 添加按钮到布局
                    layout.addWidget(download_btn)
                    layout.addWidget(collect_btn)
                    layout.setAlignment(QtCore.Qt.AlignCenter)
                    btn_widget.setLayout(layout)
                    self.ui.tableWidget_2.setCellWidget(row_index, 0, btn_widget)

                self.logger.info(f"搜索完成，找到 {len(song_info)} 首歌曲")
            else:
                self.logger.warning(f"未找到歌曲: {song_name}")
                QMessageBox.warning(self, "提示", "没有找到歌曲")

        except Exception as e:
            self.logger.error(f"搜索音乐时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"搜索音乐时发生错误: {e}")

    def btn_next_page(self):
        self.page += 1
        self.logger.info(f"切换到下一页: {self.page}")
        self.search_music()

    def btn_prev_page(self):
        self.page = max(1, self.page - 1)
        self.logger.info(f"切换到上一页: {self.page}")
        self.search_music()

    def create_download_handler(self, item):
        """
        创建下载处理器
        """

        def handler():
            self.download_music(item)

        return handler

    def download_music(self, row, type="download"):
        if type == "download":
            self.logger.info(f"开始下载音乐: {row[0]} - {row[1]}")
            msg = QMessageBox.information(
                self,
                "提示",
                f"确定下载{row[0]}---{row[1]}吗？",
                QMessageBox.Yes | QMessageBox.No
            )

            if msg == QMessageBox.Yes:
                self.save_music(row, type)
        else:
            self.save_music(row, type)

    def save_music(self, row, type="download"):
        action_str = "下载" if type == "download" else "缓存"
        save_path = self.music_dir if type == "download" else self.cache_dir
        filename = f"{row[0]}--{row[1]}.mp3"
        filepath = os.path.join(save_path, filename)
        if os.path.exists(filepath):
            return True
        try:
            response = requests.get(row[5], timeout=30)
            response.raise_for_status()  # 检查HTTP错误

            music_content = response.content

            if not os.path.exists(save_path):
                os.makedirs(save_path)

            with open(filepath, 'wb') as f:
                f.write(music_content)

            # 检查下载的文件是否为有效的二进制音频文件
            if not is_binary_file(filepath):
                # 删除无效文件
                os.remove(filepath)
                self.logger.warning(f"下载的文件不是有效的音频文件，已删除: {filepath}")
                QMessageBox.warning(self, "版权保护", f"歌曲 '{row[0]} - {row[1]}' 因版权问题无法加载")
                return False

            self.logger.info(f"音乐{action_str}成功: {filepath}")
            QMessageBox.information(self, "提示", f"{action_str}成功, 已保存至{save_path}目录下")
            return True

        except requests.RequestException as e:
            self.logger.error(f"{action_str}音乐请求失败: {e}")
            QMessageBox.critical(self, "错误", f"{action_str}音乐请求失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"{action_str}音乐时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"{action_str}音乐时发生错误: {e}")
            return False

    def clear_table(self):
        # 清空现有数据
        self.ui.tableWidget_2.setRowCount(0)
        self.logger.debug("表格已清空")

    def collect_playlist(self, row):
        """
        收藏歌单
        :param row: 歌曲信息 [title, author, pic, wording, musicing, play_url]
        """
        self.logger.info(f"开始收藏歌单: {row[0]} - {row[1]}")

        try:
            sqlite_manager = SQLiteManager(self.db_path)

            [title, author, pic, wording, musicing, play_url] = row
            data = {
                'title': title,
                'author': author,
                'pic': pic,
                'wording': wording,
                'musicing': musicing,
                'play_url': play_url
            }
            ret = self.save_music(row, type="cache")
            if ret:
                result = sqlite_manager.insert_one('tb_collect_playlist', data)
                self.logger.info(f"歌单收藏成功，ID: {result}")
                QMessageBox.information(self, "提示", "歌单收藏成功")

            # 立即刷新收藏列表
            self.load_collect_playlist()

        except Exception as e:
            self.logger.error(f"收藏歌单时发生错误: {e}")
            QMessageBox.critical(self, "错误", f"收藏歌单时发生错误: {e}")

    def load_collect_playlist(self):
        """加载收藏的歌单，带加载效果"""
        self.logger.info("开始加载收藏的歌单")

        # 显示加载提示
        self.ui.listWidget.clear()
        loading_item = QtWidgets.QListWidgetItem("加载中...")
        loading_item.setFlags(QtCore.Qt.ItemIsEnabled)
        self.ui.listWidget.addItem(loading_item)

        # 在后台线程加载数据
        self.loading_thread = LoadingPlaylistThread(self.db_path)
        self.loading_thread.data_loaded.connect(self.on_playlist_loaded)
        self.loading_thread.start()

    def on_playlist_loaded(self, data):
        """处理加载完成的数据"""
        self.ui.listWidget.clear()

        if not data:
            # 如果没有数据，显示提示
            no_data_item = QtWidgets.QListWidgetItem("暂无收藏的歌单")
            no_data_item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.ui.listWidget.addItem(no_data_item)
        else:
            for item in data:
                list_item = QtWidgets.QListWidgetItem(f"{item['title']} - {item['author']}")
                # 将完整的信息存储到Qt.UserRole中
                list_item.setData(QtCore.Qt.UserRole, item)
                self.collect_list.append(item)
                self.ui.listWidget.addItem(list_item)

        self.logger.info(f"歌单加载完成，共 {len(data)} 条记录")

    def closeEvent(self, event):
        """
        重写关闭事件，清理临时目录
        """
        self.logger.info("应用程序即将关闭")

        # 停止所有正在运行的下载线程
        if hasattr(self, 'image_threads'):
            for thread in self.image_threads:
                if thread.isRunning():
                    thread.quit()
                    thread.wait()
            self.logger.debug("所有图片下载线程已停止")

        # 删除临时目录
        if os.path.exists(self.image_dir):
            try:
                import shutil
                shutil.rmtree(self.image_dir)
                self.logger.info(f"已删除临时目录: {self.image_dir}")
            except Exception as e:
                self.logger.error(f"删除临时目录失败: {e}")

        # 调用父类的关闭事件处理
        super().closeEvent(event)
        self.logger.info("应用程序已关闭")


# 按装订区域中的绿色按钮以运行脚本。
if __name__ == '__main__':
    app = QApplication(sys.argv)
    try:
        # 创建主窗口实例
        window = MainWindow()
        window.show()  # 显示窗口
        # 进入应用程序的事件循环，保持应用程序运行，直到关闭窗口
        sys.exit(app.exec_())
    except Exception as e:
        app_logger.error(f"应用程序发生错误: {e}", exc_info=True)
        sys.exit(1)
