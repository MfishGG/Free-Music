import sqlite3
from typing import List, Tuple, Optional, Union
import os
from log_handle import app_logger  # 导入日志配置


class SQLiteManager:
    """
    SQLite数据库操作封装类
    支持单条插入、批量插入、单条查询、批量查询、单条删除、批量删除等操作
    """

    def __init__(self, db_path: str):
        """
        初始化数据库连接

        Args:
            db_path (str): 数据库文件路径
        """
        self.db_path = db_path
        self.logger = app_logger  # 使用全局logger
        self.ensure_db_exists()
        self.connection = None
        self._connect()

    def ensure_db_exists(self):
        """
        确保数据库文件存在，如果不存在则创建一个新的数据库文件
        """
        if not os.path.exists(self.db_path):
            # 如果数据库文件不存在，则创建一个新的连接会自动创建文件
            conn = sqlite3.connect(self.db_path)
            conn.close()
            self.logger.info(f"数据库文件 {self.db_path} 已创建")
        else:
            self.logger.info(f"数据库文件 {self.db_path} 已存在")

    def _connect(self):
        """建立数据库连接"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # 使结果可以通过列名访问
            self.logger.debug(f"数据库连接已建立: {self.db_path}")
        except sqlite3.Error as e:
            self.logger.error(f"数据库连接失败: {e}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.logger.debug(f"数据库连接已关闭: {self.db_path}")

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[sqlite3.Row]:
        """
        执行查询语句

        Args:
            query (str): SQL查询语句
            params (Optional[Tuple]): 查询参数

        Returns:
            List[sqlite3.Row]: 查询结果
        """
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            self.logger.debug(f"查询执行成功: {query[:50]}...")
            return results
        except sqlite3.Error as e:
            self.logger.error(f"查询执行失败: {e}, Query: {query}")
            raise

    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        执行更新语句（INSERT, UPDATE, DELETE）

        Args:
            query (str): SQL更新语句
            params (Optional[Tuple]): 参数

        Returns:
            int: 影响的行数
        """
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            affected_rows = cursor.rowcount
            self.logger.info(f"更新执行成功: {affected_rows} 行受到影响, Query: {query[:50]}...")
            return affected_rows
        except sqlite3.Error as e:
            self.connection.rollback()
            self.logger.error(f"更新执行失败: {e}, Query: {query}")
            raise

    def insert_one(self, table: str, data: dict) -> int:
        """
        单条数据插入

        Args:
            table (str): 表名
            data (dict): 插入的数据字典

        Returns:
            int: 插入记录的ID
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, tuple(data.values()))
            self.connection.commit()
            last_row_id = cursor.lastrowid
            self.logger.info(f"单条数据插入成功: 表={table}, ID={last_row_id}")
            return last_row_id
        except sqlite3.Error as e:
            self.connection.rollback()
            self.logger.error(f"单条插入失败: {e}, Table: {table}, Data: {data}")
            raise

    def insert_many(self, table_name, data_list):
        """批量插入数据，忽略重复项"""
        if not data_list:
            self.logger.debug(f"批量插入数据为空，表名: {table_name}")
            return 0

        try:
            columns = list(data_list[0].keys())
            placeholders = ', '.join(['?' for _ in columns])
            columns_str = ', '.join(columns)

            query = f"INSERT OR IGNORE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            values_list = [tuple(item[col] for col in columns) for item in data_list]

            self.logger.info(f"开始批量插入数据，表名: {table_name}, 待插入记录数: {len(data_list)}")

            with self.connection:
                cursor = self.connection.cursor()
                cursor.executemany(query, values_list)
                affected_rows = cursor.rowcount
                self.logger.info(f"批量插入完成，表名: {table_name}, 实际插入记录数: {affected_rows}")
                return affected_rows

        except sqlite3.Error as e:
            self.logger.error(f"批量插入失败: {e}, Table: {table_name}, 待插入记录数: {len(data_list)}")
            return 0



    def select_one(self, table: str, condition: str = "", params: Optional[Tuple] = None) -> Optional[sqlite3.Row]:
        """
        查询单条记录

        Args:
            table (str): 表名
            condition (str): 查询条件
            params (Optional[Tuple]): 查询参数

        Returns:
            Optional[sqlite3.Row]: 查询结果，如果没有结果则返回None
        """
        query = f"SELECT * FROM {table}"
        if condition:
            query += f" WHERE {condition}"

        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchone()
            self.logger.debug(f"单条查询执行: {query[:50]}..., Result found: {result is not None}")
            return result
        except sqlite3.Error as e:
            self.logger.error(f"单条查询失败: {e}, Query: {query}")
            raise

    def select_all(self, table: str, condition: str = "", params: Optional[Tuple] = None,
                   order_by: str = "", limit: Optional[int] = None) -> List[sqlite3.Row]:
        """
        查询多条记录

        Args:
            table (str): 表名
            condition (str): 查询条件
            params (Optional[Tuple]): 查询参数
            order_by (str): 排序规则
            limit (Optional[int]): 限制返回数量

        Returns:
            List[sqlite3.Row]: 查询结果列表
        """
        query = f"SELECT * FROM {table}"
        if condition:
            query += f" WHERE {condition}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"

        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            self.logger.debug(f"批量查询执行: {query[:50]}..., Found {len(results)} records")
            return results
        except sqlite3.Error as e:
            self.logger.error(f"批量查询失败: {e}, Query: {query}")
            raise

    def delete_one(self, table: str, condition: str, params: Optional[Tuple] = None) -> int:
        """
        删除单条记录

        Args:
            table (str): 表名
            condition (str): 删除条件
            params (Optional[Tuple]): 条件参数

        Returns:
            int: 删除的行数
        """
        query = f"DELETE FROM {table} WHERE {condition}"

        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            affected_rows = cursor.rowcount
            self.logger.info(f"单条删除执行成功: 表={table}, 删除{affected_rows}行, Condition: {condition}")
            return affected_rows
        except sqlite3.Error as e:
            self.connection.rollback()
            self.logger.error(f"单条删除失败: {e}, Query: {query}")
            raise

    def delete_many(self, table: str, condition: str, params: Optional[Tuple] = None) -> int:
        """
        批量删除记录

        Args:
            table (str): 表名
            condition (str): 删除条件
            params (Optional[Tuple]): 条件参数

        Returns:
            int: 删除的行数
        """
        query = f"DELETE FROM {table} WHERE {condition}"

        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            affected_rows = cursor.rowcount
            self.logger.info(f"批量删除执行成功: 表={table}, 删除{affected_rows}行, Condition: {condition}")
            return affected_rows
        except sqlite3.Error as e:
            self.connection.rollback()
            self.logger.error(f"批量删除失败: {e}, Query: {query}")
            raise

    def create_table(self, table_name: str, schema: str):
        """
        创建表

        Args:
            table_name (str): 表名
            schema (str): 表结构定义
        """
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
            self.logger.info(f"表创建成功或已存在: {table_name}")
        except sqlite3.Error as e:
            self.connection.rollback()
            self.logger.error(f"创建表失败: {e}, Query: {query}")
            raise

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，自动关闭连接"""
        self.close()


# 使用示例
if __name__ == "__main__":
    # 示例：如何使用SQLiteManager类
    with SQLiteManager("music.db") as db:
        # 创建示例表
        db.create_table(
            "users",
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT NOT NULL, "
            "email TEXT UNIQUE, "
            "age INTEGER"
        )

        # 单条插入
        user_id = db.insert_one("users", {"name": "张三", "email": "zhangsan@example.com", "age": 25})
        print(f"插入用户ID: {user_id}")

        # 批量插入
        users_data = [
            {"name": "李四", "email": "lisi@example.com", "age": 30},
            {"name": "王五", "email": "wangwu@example.com", "age": 28},
            {"name": "赵六", "email": "zhaoliu@example.com", "age": 35}
        ]
        inserted_count = db.insert_many("users", users_data)
        print(f"批量插入了 {inserted_count} 条记录")

        # 单条查询
        user = db.select_one("users", "name = ?", ("张三",))
        if user:
            print(f"找到用户: {user['name']}, 邮箱: {user['email']}")

        # 批量查询
        all_users = db.select_all("users", order_by="age DESC")
        print("所有用户:")
        for u in all_users:
            print(f"  ID: {u['id']}, 姓名: {u['name']}, 年龄: {u['age']}")

        # 删除单条记录
        deleted_count = db.delete_one("users", "name = ?", ("张三",))
        print(f"删除了 {deleted_count} 条记录")

        # 批量删除
        deleted_count = db.delete_many("users", "age > ?", (30,))
        print(f"批量删除了 {deleted_count} 条记录")
