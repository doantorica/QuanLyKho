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
                CREATE TABLE IF NOT EXISTS vat_tu (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    loai VARCHAR(255),
                    nha_cung_cap VARCHAR(255),
                    so_luong_ton INT DEFAULT 0
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_id INT,
                    quantity_sold INT,
                    sale_date DATE,
                    selling_price DECIMAL(15, 2),
                    customer_name VARCHAR(255),
                    customer_phone VARCHAR(20),
                    FOREIGN KEY (item_id) REFERENCES vat_tu(id) ON DELETE SET NULL
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS import_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_id INT,
                    quantity_imported INT,
                    import_date DATE,
                    import_price DECIMAL(15, 2),
                    FOREIGN KEY (item_id) REFERENCES vat_tu(id) ON DELETE SET NULL
                )
            """)
            self.conn.commit()
            self.reset_caches()
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi thiết lập bảng vật tư: {err}")

    def reset_caches(self):
        """Đặt lại toàn bộ cache với thời gian hết hạn để tự động làm mới sau 5 phút."""
        self.items_cache = None
        self.sales_cache = None
        self.import_cache = None
        self.cache_changed = {'items': True, 'sales': True, 'imports': True}
        self.last_fetch_time = time.time()

    def fetch_all_items(self, last_id=None, limit=20, force_refresh=False):
        if (time.time() - self.last_fetch_time > 300 or  # 5 phút làm mới tự động
            force_refresh or self.cache_changed['items'] or self.items_cache is None):
            try:
                query = """
                    SELECT v.id, v.loai, v.nha_cung_cap, v.so_luong_ton, i.import_price
                    FROM vat_tu v
                    LEFT JOIN (
                        SELECT item_id, MAX(import_price) as import_price
                        FROM import_history
                        GROUP BY item_id
                    ) i ON v.id = i.item_id
                    WHERE (v.id > %s OR %s IS NULL)
                    ORDER BY v.id
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

    def sell_item(self, item_id, quantity, price, customer_name, customer_phone):
        if not (isinstance(quantity, (int, float)) and quantity > 0) or price < 0:
            raise ValueError("Số lượng và giá bán phải lớn hơn 0!")
        try:
            self.cursor.execute("SELECT so_luong_ton FROM vat_tu WHERE id=%s", (item_id,))
            result = self.cursor.fetchone()
            if not result or result[0] < quantity:
                raise ValueError("Số lượng tồn kho không đủ!")
            self.cursor.execute("UPDATE vat_tu SET so_luong_ton = so_luong_ton - %s WHERE id = %s", (quantity, item_id))
            self.cursor.execute(
                "INSERT INTO sales_history (item_id, quantity_sold, sale_date, selling_price, customer_name, customer_phone) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (item_id, int(quantity), date.today(), float(price), customer_name.strip(), customer_phone.strip())
            )
            self.conn.commit()
            self.cache_changed['items'] = True
            self.cache_changed['sales'] = True
            self.reset_caches()
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi bán vật tư: {err}")

    def import_item(self, loai, nha_cung_cap, quantity, price=None):
        if not (isinstance(quantity, (int, float)) and quantity > 0):
            raise ValueError("Số lượng nhập phải lớn hơn 0!")
        if price is not None and price < 0:
            raise ValueError("Giá nhập không được âm!")
        try:
            self.cursor.execute("SELECT id, so_luong_ton FROM vat_tu WHERE loai=%s AND nha_cung_cap=%s",
                               (loai.strip(), nha_cung_cap.strip()))
            result = self.cursor.fetchone()
            if result:
                item_id, current_quantity = result
                new_quantity = current_quantity + int(quantity)
                price = float(price) if price is not None else self._get_last_import_price(item_id)
                self.cursor.execute("UPDATE vat_tu SET so_luong_ton=%s WHERE id=%s", (new_quantity, item_id))
            else:
                if price is None:
                    raise ValueError("Vật tư mới cần cung cấp giá nhập hàng!")
                self.cursor.execute(
                    "INSERT INTO vat_tu (loai, nha_cung_cap, so_luong_ton) VALUES (%s, %s, %s)",
                    (loai.strip(), nha_cung_cap.strip(), int(quantity))
                )
                self.cursor.execute("SELECT LAST_INSERT_ID()")
                item_id = self.cursor.fetchone()[0]
            self.cursor.execute(
                "INSERT INTO import_history (item_id, quantity_imported, import_date, import_price) VALUES (%s, %s, %s, %s)",
                (item_id, int(quantity), date.today(), float(price))
            )
            self.conn.commit()
            self.cache_changed['items'] = True
            self.cache_changed['imports'] = True
            self.reset_caches()
            return item_id
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi nhập hàng: {err}")

    def _get_last_import_price(self, item_id):
        """Lấy giá nhập cuối cùng cho một vật tư."""
        self.cursor.execute(
            "SELECT import_price FROM import_history WHERE item_id=%s ORDER BY import_date DESC LIMIT 1",
            (item_id,)
        )
        result = self.cursor.fetchone()
        return float(result[0]) if result else 0.0

    def fetch_sales_history(self, limit=10, force_refresh=False):
        if (time.time() - self.last_fetch_time > 300 or  # 5 phút làm mới tự động
            force_refresh or self.cache_changed['sales'] or self.sales_cache is None):
            try:
                query = """
                    SELECT v.loai, s.quantity_sold, s.sale_date, s.selling_price, 
                           s.customer_name, s.customer_phone
                    FROM sales_history s 
                    LEFT JOIN vat_tu v ON s.item_id = v.id
                    ORDER BY s.sale_date DESC
                    LIMIT %s
                """
                self.cursor.execute(query, (limit,))
                self.sales_cache = [list(row) for row in self.cursor.fetchall()]
                self.cache_changed['sales'] = False
                self.last_fetch_time = time.time()
            except mysql.connector.Error as err:
                raise Exception(f"Lỗi khi lấy lịch sử bán hàng: {err}")
        return self.sales_cache if self.sales_cache else []

    def fetch_import_history(self, limit=10, force_refresh=False):
        if (time.time() - self.last_fetch_time > 300 or  # 5 phút làm mới tự động
            force_refresh or self.cache_changed['imports'] or self.import_cache is None):
            try:
                query = """
                    SELECT v.loai, i.quantity_imported, i.import_date, i.import_price
                    FROM import_history i 
                    LEFT JOIN vat_tu v ON i.item_id = v.id
                    ORDER BY i.import_date DESC
                    LIMIT %s
                """
                self.cursor.execute(query, (limit,))
                self.import_cache = [list(row) for row in self.cursor.fetchall()]
                self.cache_changed['imports'] = False
                self.last_fetch_time = time.time()
            except mysql.connector.Error as err:
                raise Exception(f"Lỗi khi lấy lịch sử nhập hàng: {err}")
        return self.import_cache if self.import_cache else []

    def delete_item(self, item_id):
        try:
            self.cursor.execute("SELECT id FROM vat_tu WHERE id = %s", (item_id,))
            if not self.cursor.fetchone():
                raise ValueError("Vật tư không tồn tại!")
            for table in ['sales_history', 'import_history']:
                self.cursor.execute(f"DELETE FROM {table} WHERE item_id = %s", (item_id,))
            self.cursor.execute("DELETE FROM vat_tu WHERE id = %s", (item_id,))
            self.conn.commit()
            self.cache_changed['items'] = True
            self.cache_changed['sales'] = True
            self.cache_changed['imports'] = True
            self.reset_caches()
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi xóa vật tư: {err}")