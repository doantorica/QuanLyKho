import mysql.connector
from datetime import date
import time
import decimal

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

    def setup_photocopy(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS photocopy_machines (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    loai_may VARCHAR(255),
                    ten_may VARCHAR(255),
                    trang_thai VARCHAR(50) DEFAULT 'Trong Kho',
                    ngay_nhap DATE,
                    gia_nhap DECIMAL(15, 2),
                    serial_number VARCHAR(50) UNIQUE
                )
            """)
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
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS counter_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    machine_id INT,
                    counter_value INT,
                    record_date DATE,
                    FOREIGN KEY (machine_id) REFERENCES photocopy_machines(id) ON DELETE SET NULL
                )
            """)
            self.conn.commit()
            self.reset_caches()
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi thiết lập bảng máy photocopy: {err}")

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

            try:
                    LIMIT %s
                self.last_fetch_time = time.time()
            except mysql.connector.Error as err:

        try:
            self.conn.commit()
            self.cache_changed['machines'] = True
        except mysql.connector.Error as err:

        try:
            self.conn.commit()
            self.cache_changed['machines'] = True
        except mysql.connector.Error as err:

        try:
            machine = self.cursor.fetchone()
            self.conn.commit()
            self.cache_changed['machines'] = True
            self.cache_changed['rentals'] = True
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi cho thuê máy photocopy: {err}")

        try:
            self.conn.commit()
            self.cache_changed['machines'] = True
            self.cache_changed['rentals'] = True
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi trả máy photocopy: {err}")

        try:
            self.conn.commit()
            self.cache_changed['maintenance'] = True
            return True
        except mysql.connector.Error as err:

        try:
        except mysql.connector.Error as err:

        try:
            self.cursor.execute("DELETE FROM photocopy_machines WHERE id = %s", (machine_id,))
            self.conn.commit()
            self.cache_changed['machines'] = True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi xóa máy photocopy: {err}")