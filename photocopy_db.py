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
                    so_counter INT,
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

    def reset_caches(self):
        """Đặt lại toàn bộ cache với thời gian hết hạn để tự động làm mới sau 5 phút."""
        self.machines_cache = None
        self.sales_cache = None
        self.rental_cache = None
        self.maintenance_cache = None
        self.counter_cache = None
        self.cache_changed = {'machines': True, 'sales': True, 'rentals': True, 'maintenance': True, 'counter': True}
        self.last_fetch_time = time.time()

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
                        ORDER BY pm.ngay_nhap DESC
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

    def fetch_available_photocopy_machines(self, last_id=None, limit=20, force_refresh=False):
        if (time.time() - self.last_fetch_time > 300 or  # 5 phút làm mới tự động
            force_refresh or self.cache_changed['machines'] or self.machines_cache is None):
            try:
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
                raise Exception(f"Lỗi khi lấy danh sách máy photocopy có sẵn: {err}")
        if not self.machines_cache and last_id is not None:
            return self.fetch_available_photocopy_machines(None, limit, True)
        return self.machines_cache if self.machines_cache else []

    def sell_photocopy_machine(self, machine_id, quantity, selling_price, customer_name, customer_phone):
        if not (isinstance(quantity, (int, float)) and quantity > 0) or selling_price < 0:
            raise ValueError("Số lượng và giá bán phải lớn hơn 0!")
        try:
            self.cursor.execute("SELECT trang_thai, ten_may, gia_nhap FROM photocopy_machines WHERE id=%s", (machine_id,))
            machine = self.cursor.fetchone()
            if not machine or machine[0] != 'Trong Kho':
                raise ValueError("Máy không tồn tại hoặc không trong kho để bán!")
            if quantity > 1:
                raise ValueError("Hệ thống chỉ hỗ trợ bán 1 máy mỗi lần!")
            self.cursor.execute(
                "INSERT INTO photocopy_sales_history (machine_id, machine_name, sale_date, selling_price, gia_nhap, customer_name, customer_phone) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (machine_id, machine[1], date.today(), float(selling_price), float(machine[2]), customer_name.strip(), customer_phone.strip())
            )
            self.cursor.execute("DELETE FROM photocopy_machines WHERE id=%s", (machine_id,))
            self.conn.commit()
            self.cache_changed['machines'] = True
            self.cache_changed['sales'] = True
            self.reset_caches()
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi bán máy photocopy: {err}")

    def import_photocopy_machine(self, loai_may, ten_may, so_counter, gia_nhap, serial_number):
        if not (isinstance(so_counter, (int, float)) and so_counter >= 0) or gia_nhap < 0:
            raise ValueError("Số counter và giá nhập phải lớn hơn hoặc bằng 0!")
        if not serial_number or not isinstance(serial_number, str):
            raise ValueError("Số serial không được để trống và phải là chuỗi!")
        try:
            self.cursor.execute(
                "INSERT INTO photocopy_machines (loai_may, ten_may, so_counter, trang_thai, ngay_nhap, gia_nhap, serial_number) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (loai_may.strip(), ten_may.strip(), int(so_counter), 'Trong Kho', date.today(), float(gia_nhap), serial_number.strip())
            )
            self.conn.commit()
            self.cache_changed['machines'] = True
            self.reset_caches()
            self.cursor.execute("SELECT LAST_INSERT_ID()")
            return self.cursor.fetchone()[0]
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi nhập máy photocopy: {err}")

    def rent_photocopy_machine(self, machine_id, customer_name, customer_phone, start_date, end_date, rental_price):
        if not (isinstance(rental_price, (int, float)) and rental_price >= 0):
            raise ValueError("Giá thuê phải lớn hơn hoặc bằng 0!")
        try:
            self.cursor.execute("SELECT trang_thai, ten_may FROM photocopy_machines WHERE id=%s", (machine_id,))
            machine = self.cursor.fetchone()
            if not machine or machine[0] != 'Trong Kho':
                raise ValueError("Máy không tồn tại hoặc không trong kho để cho thuê!")
            self.cursor.execute("UPDATE photocopy_machines SET trang_thai='Đang Cho Thuê' WHERE id=%s", (machine_id,))
            self.cursor.execute(
                "INSERT INTO rental_history (machine_id, customer_name, customer_phone, start_date, end_date, rental_price) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (machine_id, customer_name.strip(), customer_phone.strip(), start_date, end_date, float(rental_price))
            )
            self.conn.commit()
            self.cache_changed['machines'] = True
            self.cache_changed['rentals'] = True
            self.reset_caches()
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi cho thuê máy photocopy: {err}")

    def return_photocopy_machine(self, machine_id, return_date, return_counter, return_customer_name, return_customer_phone):
        if not (isinstance(return_counter, (int, float)) and return_counter >= 0):
            raise ValueError("Số counter trả phải lớn hơn hoặc bằng 0!")
        try:
            self.cursor.execute("SELECT trang_thai, ten_may FROM photocopy_machines WHERE id=%s", (machine_id,))
            machine = self.cursor.fetchone()
            if not machine or machine[0] != 'Đang Cho Thuê':
                raise ValueError("Máy không tồn tại hoặc không đang được cho thuê!")
            self.cursor.execute(
                "UPDATE photocopy_machines SET trang_thai='Trong Kho', so_counter=%s WHERE id=%s",
                (int(return_counter), machine_id)
            )
            self.cursor.execute(
                "UPDATE rental_history SET return_date=%s, return_counter=%s, return_customer_name=%s, return_customer_phone=%s "
                "WHERE machine_id=%s AND return_date IS NULL",
                (return_date, int(return_counter), return_customer_name.strip(), return_customer_phone.strip(), machine_id)
            )
            self.conn.commit()
            self.cache_changed['machines'] = True
            self.cache_changed['rentals'] = True
            self.reset_caches()
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi trả máy photocopy: {err}")

    def add_maintenance_record(self, machine_id, description, cost):
        if not (isinstance(cost, (int, float)) and cost >= 0):
            raise ValueError("Chi phí bảo trì không được âm!")
        try:
            self.cursor.execute(
                "INSERT INTO maintenance_history (machine_id, maintenance_date, description, cost) "
                "VALUES (%s, %s, %s, %s)",
                (machine_id, date.today(), description.strip(), float(cost))
            )
            self.conn.commit()
            self.cache_changed['maintenance'] = True
            self.reset_caches()
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi thêm bảo trì: {err}")

    def fetch_photocopy_sales_history(self, limit=10, force_refresh=False):
        if (time.time() - self.last_fetch_time > 300 or  # 5 phút làm mới tự động
            force_refresh or self.cache_changed['sales'] or self.sales_cache is None):
            try:
                query = """
                    SELECT machine_name, sale_date, selling_price, customer_name, customer_phone
                    FROM photocopy_sales_history
                    ORDER BY sale_date DESC
                    LIMIT %s
                """
                self.cursor.execute(query, (limit,))
                self.sales_cache = [list(row) for row in self.cursor.fetchall()]
                self.cache_changed['sales'] = False
                self.last_fetch_time = time.time()
            except mysql.connector.Error as err:
                raise Exception(f"Lỗi khi lấy lịch sử bán máy photocopy: {err}")
        return self.sales_cache if self.sales_cache else []

    def fetch_rental_history(self, limit=10, force_refresh=False):
        if (time.time() - self.last_fetch_time > 300 or  # 5 phút làm mới tự động
            force_refresh or self.cache_changed['rentals'] or self.rental_cache is None):
            try:
                query = """
                    SELECT m.ten_may, r.customer_name, r.customer_phone, r.start_date, r.end_date, r.rental_price, 
                           r.return_date, r.return_counter, r.return_customer_name, r.return_customer_phone
                    FROM rental_history r 
                    LEFT JOIN photocopy_machines m ON r.machine_id = m.id
                    ORDER BY r.start_date DESC
                    LIMIT %s
                """
                self.cursor.execute(query, (limit,))
                self.rental_cache = [list(row) for row in self.cursor.fetchall()]
                self.cache_changed['rentals'] = False
                self.last_fetch_time = time.time()
            except mysql.connector.Error as err:
                raise Exception(f"Lỗi khi lấy lịch sử cho thuê máy photocopy: {err}")
        return self.rental_cache if self.rental_cache else []

    def fetch_maintenance_history(self, machine_id=None, limit=10, force_refresh=False):
        if (time.time() - self.last_fetch_time > 300 or  # 5 phút làm mới tự động
            force_refresh or self.cache_changed['maintenance'] or self.maintenance_cache is None):
            try:
                query = """
                    SELECT m.ten_may, mh.maintenance_date, mh.description, mh.cost
                    FROM maintenance_history mh
                    LEFT JOIN photocopy_machines m ON mh.machine_id = m.id
                """
                if machine_id:
                    query += " WHERE mh.machine_id = %s"
                    self.cursor.execute(query, (machine_id,))
                else:
                    query += " ORDER BY mh.maintenance_date DESC LIMIT %s"
                    self.cursor.execute(query, (limit,))
                self.maintenance_cache = [list(row) for row in self.cursor.fetchall()]
                self.cache_changed['maintenance'] = False
                self.last_fetch_time = time.time()
            except mysql.connector.Error as err:
                raise Exception(f"Lỗi khi lấy lịch sử bảo trì: {err}")
        if machine_id:
            return [row for row in self.maintenance_cache if row[0] == machine_id] if self.maintenance_cache else []
        return self.maintenance_cache if self.maintenance_cache else []

    def delete_photocopy_machine(self, machine_id):
        try:
            self.cursor.execute("SELECT trang_thai, ten_may FROM photocopy_machines WHERE id=%s", (machine_id,))
            machine = self.cursor.fetchone()
            if not machine or machine[0] == 'Đang Cho Thuê':
                raise ValueError("Máy không tồn tại hoặc đang được cho thuê, không thể xóa!")
            self.cursor.execute("DELETE FROM photocopy_machines WHERE id=%s", (machine_id,))
            self.conn.commit()
            self.cache_changed['machines'] = True
            self.reset_caches()
            return True
        except mysql.connector.Error as err:
            raise Exception(f"Lỗi khi xóa máy photocopy: {err}")