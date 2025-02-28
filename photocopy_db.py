import mysql.connector
from datetime import date
import time
import decimal
from functools import lru_cache
import logging
import PySimpleGUI as sg

class PhotocopyDatabase:
    def __init__(self, connection):
        self.conn = connection
        self.cursor = self.conn.cursor()
        self.machines_cache = None
        self.sales_cache = None
        self.rental_cache = None
        self.maintenance_cache = None
        self.counter_cache = None
        self.cache_changed = {'machines': True, 'sales': True, 'rentals': True, 'maintenance': True, 'counter': True}
        self.last_fetch_time = 0

    def reset_caches(self):
        self.machines_cache = None
        self.sales_cache = None
        self.rental_cache = None
        self.maintenance_cache = None
        self.counter_cache = None
        self.cache_changed = {'machines': True, 'sales': True, 'rentals': True, 'maintenance': True, 'counter': True}
        self.last_fetch_time = 0

    def setup_photocopy(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS photocopy_machines (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    loai_may VARCHAR(255),
                    ten_may VARCHAR(255),
                    so_counter INT DEFAULT 0,
                    trang_thai VARCHAR(50) DEFAULT 'Trong Kho',
                    ngay_nhap DATE,
                    gia_nhap DECIMAL(15, 2),
                    serial_number VARCHAR(50) UNIQUE
                )
            """)
            # Kiểm tra và tạo chỉ mục nếu chưa tồn tại
            try:
                self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_id ON photocopy_machines(id)")
                self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_trang_thai ON photocopy_machines(trang_thai)")
            except mysql.connector.Error as index_err:
                logging.warning(f"Chỉ mục idx_id hoặc idx_trang_thai đã tồn tại hoặc lỗi: {index_err}")
                sg.popup_error(f"Chỉ mục cho bảng máy photocopy đã tồn tại hoặc lỗi: {index_err}")

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS photocopy_sales_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    machine_id INT,
                    machine_name VARCHAR(255),
                    sale_date DATE,
                    selling_price DECIMAL(15, 2),
                    gia_nhap DECIMAL(15, 2),
                    customer_name VARCHAR(255),
                    customer_phone VARCHAR(20),
                    FOREIGN KEY (machine_id) REFERENCES photocopy_machines(id) ON DELETE SET NULL
                )
            """)
            try:
                self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_machine_id ON photocopy_sales_history(machine_id)")
            except mysql.connector.Error as index_err:
                logging.warning(f"Chỉ mục idx_machine_id cho photocopy_sales_history đã tồn tại hoặc lỗi: {index_err}")
                sg.popup_error(f"Chỉ mục cho lịch sử bán máy photocopy đã tồn tại hoặc lỗi: {index_err}")

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS rental_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    machine_id INT,
                    customer_name VARCHAR(255),
                    customer_phone VARCHAR(20),
                    start_date DATE,
                    end_date DATE,
                    rental_price DECIMAL(15, 2),
                    return_date DATE DEFAULT NULL,
                    return_counter INT DEFAULT NULL,
                    return_customer_name VARCHAR(255),
                    return_customer_phone VARCHAR(20),
                    FOREIGN KEY (machine_id) REFERENCES photocopy_machines(id) ON DELETE SET NULL
                )
            """)
            try:
                self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_machine_id ON rental_history(machine_id)")
            except mysql.connector.Error as index_err:
                logging.warning(f"Chỉ mục idx_machine_id cho rental_history đã tồn tại hoặc lỗi: {index_err}")
                sg.popup_error(f"Chỉ mục cho lịch sử cho thuê đã tồn tại hoặc lỗi: {index_err}")

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS maintenance_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    machine_id INT,
                    maintenance_date DATE,
                    description TEXT,
                    cost DECIMAL(15, 2),
                    FOREIGN KEY (machine_id) REFERENCES photocopy_machines(id) ON DELETE SET NULL
                )
            """)
            try:
                self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_machine_id ON maintenance_history(machine_id)")
            except mysql.connector.Error as index_err:
                logging.warning(f"Chỉ mục idx_machine_id cho maintenance_history đã tồn tại hoặc lỗi: {index_err}")
                sg.popup_error(f"Chỉ mục cho lịch sử bảo trì đã tồn tại hoặc lỗi: {index_err}")

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS counter_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    machine_id INT,
                    counter_value INT,
                    record_date DATE,
                    FOREIGN KEY (machine_id) REFERENCES photocopy_machines(id) ON DELETE SET NULL
                )
            """)
            try:
                self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_machine_id ON counter_history(machine_id)")
            except mysql.connector.Error as index_err:
                logging.warning(f"Chỉ mục idx_machine_id cho counter_history đã tồn tại hoặc lỗi: {index_err}")
                sg.popup_error(f"Chỉ mục cho lịch sử counter đã tồn tại hoặc lỗi: {index_err}")

            self.conn.commit()
            self.reset_caches()
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi thiết lập bảng máy photocopy: {err}")

    @lru_cache(maxsize=128)
    def fetch_all_photocopy_machines(self, last_id=None, limit=20, force_refresh=False, include_sold=False):
        if (time.time() - self.last_fetch_time > 300 or  # 5 phút làm mới tự động
            force_refresh or self.cache_changed['machines'] or self.machines_cache is None):
            try:
                if include_sold:
                    query = """
                        SELECT pm.id, pm.loai_may, pm.ten_may, pm.so_counter, pm.trang_thai, pm.ngay_nhap, pm.gia_nhap, pm.serial_number
                        FROM photocopy_machines pm
                        WHERE pm.trang_thai IN ('Trong Kho', 'Đã Bán') AND (pm.id > %s OR %s IS NULL)
                        UNION
                        SELECT psh.machine_id, pm.loai_may, pm.ten_may, pm.so_counter, 'Đã Bán', psh.sale_date, pm.gia_nhap, pm.serial_number
                        FROM photocopy_sales_history psh
                        LEFT JOIN photocopy_machines pm ON psh.machine_id = pm.id
                        WHERE (psh.machine_id > %s OR %s IS NULL)
                        ORDER BY COALESCE(pm.ngay_nhap, psh.sale_date) DESC
                        LIMIT %s
                    """
                    self.cursor.execute(query, (last_id, last_id, last_id, last_id, limit))
                else:
                    query = """
                        SELECT id, loai_may, ten_may, so_counter, trang_thai, ngay_nhap, gia_nhap, serial_number
                        FROM photocopy_machines
                        WHERE trang_thai = 'Trong Kho' AND (id > %s OR %s IS NULL)
                        ORDER BY ngay_nhap DESC
                        LIMIT %s
                    """
                    self.cursor.execute(query, (last_id, last_id, limit))
                self.machines_cache = [list(row) for row in self.cursor.fetchall()]
                self.cache_changed['machines'] = False
                self.last_fetch_time = time.time()
            except mysql.connector.Error as err:
                raise Exception(f"Lỗi khi lấy danh sách máy photocopy: {err}")
        if not self.machines_cache and last_id is not None:
            return self.fetch_all_photocopy_machines(None, limit, True, include_sold)
        return self.machines_cache if self.machines_cache else []

    def fetch_photocopy_sales_history(self, limit=10, force_refresh=False):
        if (time.time() - self.last_fetch_time > 300 or
            force_refresh or self.cache_changed['sales'] or self.sales_cache is None):
            try:
                self.cursor.execute("""
                    SELECT id, machine_id, machine_name, sale_date, selling_price, gia_nhap, customer_name, customer_phone
                    FROM photocopy_sales_history
                    ORDER BY sale_date DESC
                    LIMIT %s
                """, (limit,))
                self.sales_cache = [list(row) for row in self.cursor.fetchall()]
                self.cache_changed['sales'] = False
                self.last_fetch_time = time.time()
            except mysql.connector.Error as err:
                raise Exception(f"Lỗi khi lấy lịch sử bán máy photocopy: {err}")
        return self.sales_cache if self.sales_cache else []

    def fetch_rental_history(self, limit=10, force_refresh=False):
        if (time.time() - self.last_fetch_time > 300 or
            force_refresh or self.cache_changed['rentals'] or self.rental_cache is None):
            try:
                self.cursor.execute("""
                    SELECT id, machine_id, customer_name, customer_phone, start_date, end_date, rental_price, return_date, return_counter, return_customer_name, return_customer_phone
                    FROM rental_history
                    ORDER BY start_date DESC
                    LIMIT %s
                """, (limit,))
                self.rental_cache = [list(row) for row in self.cursor.fetchall()]
                self.cache_changed['rentals'] = False
                self.last_fetch_time = time.time()
            except mysql.connector.Error as err:
                raise Exception(f"Lỗi khi lấy lịch sử cho thuê: {err}")
        return self.rental_cache if self.rental_cache else []

    # Giữ nguyên các phương thức khác (add_photocopy_machine, sell_photocopy, rent_photocopy, v.v.)
    def add_photocopy_machine(self, loai_may, ten_may, so_counter, gia_nhap, serial_number, ngay_nhap=None):
        try:
            if not ngay_nhap:
                ngay_nhap = date.today()
            self.cursor.execute("""
                INSERT INTO photocopy_machines (loai_may, ten_may, so_counter, trang_thai, ngay_nhap, gia_nhap, serial_number)
                VALUES (%s, %s, %s, 'Trong Kho', %s, %s, %s)
            """, (loai_may, ten_may, so_counter, ngay_nhap, gia_nhap, serial_number))
            self.conn.commit()
            self.cache_changed['machines'] = True
            return self.cursor.lastrowid
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi thêm máy photocopy: {err}")

    def sell_photocopy(self, machine_id, selling_price, customer_name, customer_phone, sale_date=None):
        try:
            if not sale_date:
                sale_date = date.today()
            self.cursor.execute("SELECT ten_may, gia_nhap FROM photocopy_machines WHERE id = %s AND trang_thai = 'Trong Kho'", (machine_id,))
            machine = self.cursor.fetchone()
            if not machine:
                raise Exception("Máy photocopy không tồn tại hoặc đã được bán!")
            machine_name, gia_nhap = machine
            self.cursor.execute("""
                UPDATE photocopy_machines SET trang_thai = 'Đã Bán' WHERE id = %s
            """, (machine_id,))
            self.cursor.execute("""
                INSERT INTO photocopy_sales_history (machine_id, machine_name, sale_date, selling_price, gia_nhap, customer_name, customer_phone)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (machine_id, machine_name, sale_date, selling_price, gia_nhap, customer_name, customer_phone))
            self.conn.commit()
            self.cache_changed['machines'] = True
            self.cache_changed['sales'] = True
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi bán máy photocopy: {err}")

    def rent_photocopy(self, machine_id, customer_name, customer_phone, rental_price, start_date=None, end_date=None):
        try:
            if not start_date:
                start_date = date.today()
            self.cursor.execute("SELECT ten_may FROM photocopy_machines WHERE id = %s AND trang_thai = 'Trong Kho'", (machine_id,))
            machine = self.cursor.fetchone()
            if not machine:
                raise Exception("Máy photocopy không tồn tại hoặc không trong kho!")
            machine_name = machine[0]
            self.cursor.execute("""
                UPDATE photocopy_machines SET trang_thai = 'Đang Thuê' WHERE id = %s
            """, (machine_id,))
            self.cursor.execute("""
                INSERT INTO rental_history (machine_id, customer_name, customer_phone, start_date, end_date, rental_price)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (machine_id, customer_name, customer_phone, start_date, end_date, rental_price))
            self.conn.commit()
            self.cache_changed['machines'] = True
            self.cache_changed['rentals'] = True
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi cho thuê máy photocopy: {err}")

    def return_photocopy(self, machine_id, return_counter, return_customer_name, return_customer_phone, return_date=None):
        try:
            if not return_date:
                return_date = date.today()
            self.cursor.execute("""
                UPDATE photocopy_machines SET trang_thai = 'Trong Kho', so_counter = %s WHERE id = %s AND trang_thai = 'Đang Thuê'
            """, (return_counter, machine_id))
            self.cursor.execute("""
                UPDATE rental_history SET return_date = %s, return_counter = %s, return_customer_name = %s, return_customer_phone = %s
                WHERE machine_id = %s AND return_date IS NULL
            """, (return_date, return_counter, return_customer_name, return_customer_phone, machine_id))
            self.conn.commit()
            self.cache_changed['machines'] = True
            self.cache_changed['rentals'] = True
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi trả máy photocopy: {err}")

    def maintain_photocopy(self, machine_id, maintenance_date, description, cost):
        try:
            self.cursor.execute("""
                INSERT INTO maintenance_history (machine_id, maintenance_date, description, cost)
                VALUES (%s, %s, %s, %s)
            """, (machine_id, maintenance_date, description, cost))
            self.conn.commit()
            self.cache_changed['maintenance'] = True
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi bảo trì máy photocopy: {err}")

    def update_counter(self, machine_id, counter_value, record_date=None):
        try:
            if not record_date:
                record_date = date.today()
            self.cursor.execute("""
                UPDATE photocopy_machines SET so_counter = %s WHERE id = %s
            """, (counter_value, machine_id))
            self.cursor.execute("""
                INSERT INTO counter_history (machine_id, counter_value, record_date)
                VALUES (%s, %s, %s)
            """, (machine_id, counter_value, record_date))
            self.conn.commit()
            self.cache_changed['counter'] = True
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi cập nhật counter: {err}")

    def delete_photocopy(self, machine_id):
        try:
            self.cursor.execute("DELETE FROM photocopy_machines WHERE id = %s", (machine_id,))
            self.conn.commit()
            self.cache_changed['machines'] = True
            return self.cursor.rowcount > 0
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi xóa máy photocopy: {err}")