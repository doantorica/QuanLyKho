import mysql.connector
from datetime import date
import time
import decimal

class InventoryDatabase:
    def __init__(self, connection):
        self.conn = connection
        self.cursor = self.conn.cursor()
        self.items_cache = None
        self.sales_cache = None
        self.import_cache = None
        self.cache_changed = {'items': True, 'sales': True, 'imports': True}
        self.last_fetch_time = 0

    def setup_inventory(self):
        try:
            self.cursor.execute("""
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    loai VARCHAR(255),
                    nha_cung_cap VARCHAR(255),
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_id INT,
                    sale_date DATE,
                    customer_name VARCHAR(255),
                    customer_phone VARCHAR(20),
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS import_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_id INT,
                    import_date DATE,
                )
            """)
            self.conn.commit()
            self.reset_caches()
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi thiết lập bảng vật tư: {err}")

    def fetch_all_items(self, last_id=None, limit=20, force_refresh=False):
        if (time.time() - self.last_fetch_time > 300 or  # 5 phút làm mới tự động
            force_refresh or self.cache_changed['items'] or self.items_cache is None):
            try:
                query = """
                    LIMIT %s
                """
                self.cursor.execute(query, (last_id, last_id, limit))
                self.items_cache = [list(row) for row in self.cursor.fetchall()]
                self.cache_changed['items'] = False
                self.last_fetch_time = time.time()
            except mysql.connector.Error as err:
                raise Exception(f"Lỗi khi lấy danh sách vật tư: {err}")
        if not self.items_cache and last_id is not None:
            return self.fetch_all_items(None, limit, True)
        return self.items_cache if self.items_cache else []

    def fetch_sales_history(self, limit=10, force_refresh=False):
            force_refresh or self.cache_changed['sales'] or self.sales_cache is None):
            try:
                    LIMIT %s
                self.sales_cache = [list(row) for row in self.cursor.fetchall()]
                self.cache_changed['sales'] = False
                self.last_fetch_time = time.time()
            except mysql.connector.Error as err:
        return self.sales_cache if self.sales_cache else []

    def fetch_import_history(self, limit=10, force_refresh=False):
            force_refresh or self.cache_changed['imports'] or self.import_cache is None):
            try:
                    LIMIT %s
                self.import_cache = [list(row) for row in self.cursor.fetchall()]
                self.cache_changed['imports'] = False
                self.last_fetch_time = time.time()
            except mysql.connector.Error as err:
        return self.import_cache if self.import_cache else []

        try:
            self.conn.commit()
            self.cache_changed['items'] = True
            self.cache_changed['sales'] = True
            self.cache_changed['imports'] = True
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi xóa vật tư: {err}")