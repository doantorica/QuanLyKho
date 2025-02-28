import mysql.connector
from datetime import date
import time
import decimal
from functools import lru_cache
import logging
import PySimpleGUI as sg

class InventoryDatabase:
    def __init__(self, connection):
        self.conn = connection
        self.cursor = self.conn.cursor()
        self.items_cache = None
        self.sales_cache = None
        self.import_cache = None
        self.cache_changed = {'items': True, 'sales': True, 'imports': True}
        self.last_fetch_time = 0

    def reset_caches(self):
        self.items_cache = None
        self.sales_cache = None
        self.import_cache = None
        self.cache_changed = {'items': True, 'sales': True, 'imports': True}
        self.last_fetch_time = 0

    def setup_inventory(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    loai VARCHAR(255),
                    nha_cung_cap VARCHAR(255),
                    so_luong INT DEFAULT 0,
                    gia_nhap DECIMAL(15, 2),
                    ngay_nhap DATE
                )
            """)
            # Kiểm tra và tạo chỉ mục nếu chưa tồn tại
            try:
                self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_id ON inventory_items(id)")
                self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_loai ON inventory_items(loai)")
            except mysql.connector.Error as index_err:
                logging.warning(f"Chỉ mục idx_id hoặc idx_loai đã tồn tại hoặc lỗi: {index_err}")
                sg.popup_error(f"Chỉ mục cho bảng vật tư đã tồn tại hoặc lỗi: {index_err}")

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_id INT,
                    quantity INT,
                    sale_date DATE,
                    price DECIMAL(15, 2),
                    customer_name VARCHAR(255),
                    customer_phone VARCHAR(20),
                    FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE SET NULL
                )
            """)
            try:
                self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_id ON sales_history(item_id)")
            except mysql.connector.Error as index_err:
                logging.warning(f"Chỉ mục idx_item_id cho sales_history đã tồn tại hoặc lỗi: {index_err}")
                sg.popup_error(f"Chỉ mục cho lịch sử bán đã tồn tại hoặc lỗi: {index_err}")

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS import_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_id INT,
                    quantity INT,
                    import_date DATE,
                    price DECIMAL(15, 2),
                    FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE SET NULL
                )
            """)
            try:
                self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_id ON import_history(item_id)")
            except mysql.connector.Error as index_err:
                logging.warning(f"Chỉ mục idx_item_id cho import_history đã tồn tại hoặc lỗi: {index_err}")
                sg.popup_error(f"Chỉ mục cho lịch sử nhập đã tồn tại hoặc lỗi: {index_err}")

            self.conn.commit()
            self.reset_caches()
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi thiết lập bảng vật tư: {err}")

    @lru_cache(maxsize=128)
    def fetch_all_items(self, last_id=None, limit=20, force_refresh=False):
        if (time.time() - self.last_fetch_time > 300 or  # 5 phút làm mới tự động
            force_refresh or self.cache_changed['items'] or self.items_cache is None):
            try:
                query = """
                    SELECT id, loai, nha_cung_cap, so_luong, gia_nhap, ngay_nhap
                    FROM inventory_items
                    WHERE (id > %s OR %s IS NULL)
                    ORDER BY ngay_nhap DESC
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
        if (time.time() - self.last_fetch_time > 300 or
            force_refresh or self.cache_changed['sales'] or self.sales_cache is None):
            try:
                self.cursor.execute("""
                    SELECT id, item_id, quantity, sale_date, price, customer_name, customer_phone
                    FROM sales_history
                    ORDER BY sale_date DESC
                    LIMIT %s
                """, (limit,))
                self.sales_cache = [list(row) for row in self.cursor.fetchall()]
                self.cache_changed['sales'] = False
                self.last_fetch_time = time.time()
            except mysql.connector.Error as err:
                raise Exception(f"Lỗi khi lấy lịch sử bán: {err}")
        return self.sales_cache if self.sales_cache else []

    def fetch_import_history(self, limit=10, force_refresh=False):
        if (time.time() - self.last_fetch_time > 300 or
            force_refresh or self.cache_changed['imports'] or self.import_cache is None):
            try:
                self.cursor.execute("""
                    SELECT id, item_id, quantity, import_date, price
                    FROM import_history
                    ORDER BY import_date DESC
                    LIMIT %s
                """, (limit,))
                self.import_cache = [list(row) for row in self.cursor.fetchall()]
                self.cache_changed['imports'] = False
                self.last_fetch_time = time.time()
            except mysql.connector.Error as err:
                raise Exception(f"Lỗi khi lấy lịch sử nhập: {err}")
        return self.import_cache if self.import_cache else []

    # Giữ nguyên các phương thức khác (add_item, sell_item, import_item, v.v.)
    def add_item(self, loai, nha_cung_cap, so_luong, gia_nhap, ngay_nhap=None):
        try:
            if not ngay_nhap:
                ngay_nhap = date.today()
            self.cursor.execute("""
                INSERT INTO inventory_items (loai, nha_cung_cap, so_luong, gia_nhap, ngay_nhap)
                VALUES (%s, %s, %s, %s, %s)
            """, (loai, nha_cung_cap, so_luong, gia_nhap, ngay_nhap))
            self.conn.commit()
            self.cache_changed['items'] = True
            return self.cursor.lastrowid
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi thêm vật tư: {err}")

    def sell_item(self, item_id, quantity, price, customer_name, customer_phone, sale_date=None):
        try:
            if not sale_date:
                sale_date = date.today()
            # Kiểm tra số lượng tồn
            self.cursor.execute("SELECT so_luong FROM inventory_items WHERE id = %s", (item_id,))
            current_quantity = self.cursor.fetchone()
            if not current_quantity or current_quantity[0] < quantity:
                raise Exception("Số lượng tồn không đủ để bán!")
            # Giảm số lượng tồn
            self.cursor.execute("""
                UPDATE inventory_items SET so_luong = so_luong - %s WHERE id = %s
            """, (quantity, item_id))
            # Ghi lịch sử bán
            self.cursor.execute("""
                INSERT INTO sales_history (item_id, quantity, sale_date, price, customer_name, customer_phone)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (item_id, quantity, sale_date, price, customer_name, customer_phone))
            self.conn.commit()
            self.cache_changed['items'] = True
            self.cache_changed['sales'] = True
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi bán vật tư: {err}")

    def import_item(self, item_id, quantity, price, import_date=None):
        try:
            if not import_date:
                import_date = date.today()
            # Tăng số lượng tồn
            self.cursor.execute("""
                UPDATE inventory_items SET so_luong = so_luong + %s WHERE id = %s
            """, (quantity, item_id))
            # Ghi lịch sử nhập
            self.cursor.execute("""
                INSERT INTO import_history (item_id, quantity, import_date, price)
                VALUES (%s, %s, %s, %s)
            """, (item_id, quantity, import_date, price))
            self.conn.commit()
            self.cache_changed['items'] = True
            self.cache_changed['imports'] = True
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi nhập vật tư: {err}")

    def delete_item(self, item_id):
        try:
            self.cursor.execute("DELETE FROM inventory_items WHERE id = %s", (item_id,))
            self.conn.commit()
            self.cache_changed['items'] = True
            return self.cursor.rowcount > 0
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi xóa vật tư: {err}")