import mysql.connector
import PySimpleGUI as sg
import pandas as pd
from datetime import date
import time
import logging
import bcrypt

logging.basicConfig(
    filename='app.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "quan_ly_vat_tu"
}

PRODUCT_TYPES = ["Drum Color", "Drum Bk", "Mực Vàng", "Mực Đỏ", "Mực Xanh", "Mực Đen",
                 "Gạt Drum color", "Gạt Drum Bk", "Gạt Flim", "Flim Sấy", "Flim ảnh"]


class InventoryManager:
    def __init__(self, connection):
        self.conn = connection
        self.cursor = self.conn.cursor()
        self.items_cache = None
        self.sales_cache = None
        self.import_cache = None
        self.machines_cache = None
        self.photocopy_sales_cache = None
        self.rental_cache = None
        self.maintenance_cache = None
        self.counter_cache = None  # Thêm cache cho counter
        self.cache_timeout = 60
        self.last_fetch_time = 0
        self.cache_changed = {'items': False, 'machines': False, 'sales': False, 'imports': False,
                              'photocopy_sales': False, 'rentals': False, 'maintenance': False, 'counter': False}

    def setup_database(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE,
                    password VARCHAR(64),
                    role ENUM('admin', 'user') DEFAULT 'user'
                )
            """)
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
            if self.cursor.fetchone()[0] == 0:
                hashed_password = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
                self.cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                                    ('admin', hashed_password, 'admin'))
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
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS photocopy_machines (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    loai_may VARCHAR(255),
                    ten_may VARCHAR(255),
                    so_counter INT,
                    trang_thai VARCHAR(50) NOT NULL DEFAULT 'Trong Kho',
                    ngay_nhap DATE,
                    gia_nhap DECIMAL(15, 2),
                    serial_number VARCHAR(50) UNIQUE,
                    maintenance_interval INT DEFAULT 90,  # Thêm khoảng bảo trì (ngày)
                    last_maintenance_date DATE  # Thêm ngày bảo trì cuối
                )
            """)
            self.cursor.execute("SHOW COLUMNS FROM photocopy_machines LIKE 'serial_number'")
            if not self.cursor.fetchone():
                self.cursor.execute("ALTER TABLE photocopy_machines ADD COLUMN serial_number VARCHAR(50) UNIQUE")
            self.cursor.execute("SHOW COLUMNS FROM photocopy_machines LIKE 'maintenance_interval'")
            if not self.cursor.fetchone():
                self.cursor.execute("ALTER TABLE photocopy_machines ADD COLUMN maintenance_interval INT DEFAULT 90")
            self.cursor.execute("SHOW COLUMNS FROM photocopy_machines LIKE 'last_maintenance_date'")
            if not self.cursor.fetchone():
                self.cursor.execute("ALTER TABLE photocopy_machines ADD COLUMN last_maintenance_date DATE")
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
            self.cursor.execute("SHOW COLUMNS FROM photocopy_sales_history LIKE 'gia_nhap'")
            if not self.cursor.fetchone():
                self.cursor.execute("ALTER TABLE photocopy_sales_history ADD COLUMN gia_nhap DECIMAL(15, 2)")
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
            self.cursor.execute("SHOW COLUMNS FROM rental_history LIKE 'return_customer_name'")
            if not self.cursor.fetchone():
                self.cursor.execute("ALTER TABLE rental_history ADD COLUMN return_customer_name VARCHAR(255)")
            self.cursor.execute("SHOW COLUMNS FROM rental_history LIKE 'return_customer_phone'")
            if not self.cursor.fetchone():
                self.cursor.execute("ALTER TABLE rental_history ADD COLUMN return_customer_phone VARCHAR(20)")
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
            print("Database đã được thiết lập thành công!")
        except mysql.connector.Error as err:
            logging.error(f"Error setting up database: {err}")
            sg.popup_error(f"Lỗi thiết lập database: {err}")
            print(f"Lỗi thiết lập database: {err}")

    def authenticate_user(self, username, password):
        try:
            self.cursor.execute("SELECT password, role FROM users WHERE username = %s", (username,))
            result = self.cursor.fetchone()
            if result and bcrypt.checkpw(password.encode(), result[0].encode()):
                print(f"Debug - Login successful for {username} with role: {result[1]}")
                return result[1]
            else:
                print(f"Debug - Login failed for {username}: Password mismatch or user not found")
                return None
        except mysql.connector.Error as err:
            logging.error(f"Error authenticating user {username}: {err}")
            sg.popup_error(f"Lỗi xác thực người dùng: {err}")
            return None

    def fetch_counter_history(self, machine_id, force_refresh=False):
        """Lấy lịch sử counter của một máy"""
        current_time = time.time()
        if force_refresh or self.counter_cache is None or (current_time - self.last_fetch_time > self.cache_timeout) or \
                self.cache_changed['counter']:
            try:
                query = """
                    SELECT record_date, counter_value
                    FROM counter_history
                    WHERE machine_id = %s
                    ORDER BY record_date DESC
                """
                self.cursor.execute(query, (machine_id,))
                self.counter_cache = [list(item) for item in self.cursor.fetchall()]
                self.last_fetch_time = current_time
                self.cache_changed['counter'] = False
                print(f"Đã làm mới lịch sử counter cho máy ID {machine_id}: {len(self.counter_cache)} mục")
            except mysql.connector.Error as err:
                logging.error(f"Error fetching counter history for machine ID {machine_id}: {err}")
                return []
        return self.counter_cache if self.counter_cache is not None else []

    def fetch_all_items(self, offset=0, limit=20, force_refresh=False):
        current_time = time.time()
        if force_refresh or self.items_cache is None or (current_time - self.last_fetch_time > self.cache_timeout) or \
                self.cache_changed['items']:
            try:
                query = """
                    SELECT v.id, v.loai, v.nha_cung_cap, v.so_luong_ton, i.import_price as gia_nhap
                    FROM vat_tu v
                    LEFT JOIN (
                        SELECT item_id, import_price
                        FROM import_history
                        WHERE (item_id, import_date) IN (
                            SELECT item_id, MAX(import_date)
                            FROM import_history
                            GROUP BY item_id
                        )
                    ) i ON v.id = i.item_id
                    LIMIT %s OFFSET %s
                """
                self.cursor.execute(query, (limit, offset))
                self.items_cache = [list(item) for item in self.cursor.fetchall()]
                self.last_fetch_time = current_time
                self.cache_changed['items'] = False
                print(f"Đã làm mới danh sách vật tư: {len(self.items_cache)} mục (offset={offset}, limit={limit})")
            except mysql.connector.Error as err:
                logging.error(f"Error fetching all items: {err}")
                sg.popup_error(f"Lỗi khi lấy dữ liệu: {err}")
                self.items_cache = []
        return self.items_cache if self.items_cache is not None else []

    def import_photocopy_machine(self, loai_may, ten_may, so_counter, gia_nhap, serial_number):
        if so_counter < 0 or gia_nhap < 0:
            sg.popup_error("Số counter và giá nhập phải lớn hơn hoặc bằng 0!")
            return None
        if not serial_number:
            sg.popup_error("Số serial không được để trống!")
            return None
        try:
            self.cursor.execute(
                "INSERT INTO photocopy_machines (loai_may, ten_may, so_counter, trang_thai, ngay_nhap, gia_nhap, serial_number) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (loai_may, ten_may, so_counter, 'Trong Kho', date.today(), gia_nhap, serial_number)
            )
            self.cursor.execute(
                "INSERT INTO counter_history (machine_id, counter_value, record_date) "
                "VALUES (LAST_INSERT_ID(), %s, %s)",
                (so_counter, date.today())
            )
            self.conn.commit()
            self.machines_cache = None
            self.counter_cache = None
            self.cache_changed['machines'] = True
            self.cache_changed['counter'] = True
            self.cursor.execute("SELECT LAST_INSERT_ID()")
            machine_id = self.cursor.fetchone()[0]
            print(f"Đã nhập máy photocopy ID {machine_id}: {ten_may} với số serial {serial_number}")
            return machine_id
        except mysql.connector.Error as err:
            logging.error(f"Error importing photocopy machine: {err}")
            sg.popup_error(f"Lỗi khi nhập máy photocopy: {err}")
            return None

    def fetch_all_photocopy_machines(self, offset=0, limit=20, force_refresh=False, include_sold=False):
        current_time = time.time()
        if force_refresh or self.machines_cache is None or (current_time - self.last_fetch_time > self.cache_timeout) or \
                self.cache_changed['machines']:
            try:
                if include_sold:
                    query = """
                        SELECT pm.id, pm.loai_may, pm.ten_may, pm.so_counter, pm.trang_thai, pm.ngay_nhap, pm.gia_nhap, pm.serial_number
                        FROM photocopy_machines pm
                        WHERE pm.trang_thai = 'Trong Kho'
                        UNION
                        SELECT psh.machine_id, pm.loai_may, pm.ten_may, pm.so_counter, 'Đã Bán', psh.sale_date, pm.gia_nhap, pm.serial_number
                        FROM photocopy_sales_history psh
                        LEFT JOIN photocopy_machines pm ON psh.machine_id = pm.id
                        ORDER BY ngay_nhap DESC
                        LIMIT %s OFFSET %s
                    """
                else:
                    query = """
                        SELECT id, loai_may, ten_may, so_counter, trang_thai, ngay_nhap, gia_nhap, serial_number
                        FROM photocopy_machines
                        WHERE trang_thai = 'Trong Kho'
                        ORDER BY ngay_nhap DESC
                        LIMIT %s OFFSET %s
                    """
                self.cursor.execute(query, (limit, offset))
                self.machines_cache = [list(item) for item in self.cursor.fetchall()]
                self.last_fetch_time = current_time
                self.cache_changed['machines'] = False
                print(
                    f"Đã làm mới danh sách máy photocopy{' (bao gồm máy đã bán)' if include_sold else ''}: {len(self.machines_cache)} mục (offset={offset}, limit={limit})")
            except mysql.connector.Error as err:
                logging.error(f"Error fetching photocopy machines: {err}")
                sg.popup_error(f"Lỗi khi lấy danh sách máy photocopy: {err}")
                self.machines_cache = []
        return self.machines_cache if self.machines_cache is not None else []

    def fetch_available_photocopy_machines(self, offset=0, limit=20, force_refresh=False):
        current_time = time.time()
        if force_refresh or self.machines_cache is None or (current_time - self.last_fetch_time > self.cache_timeout) or \
                self.cache_changed['machines']:
            try:
                query = """
                    SELECT id, loai_may, ten_may, so_counter, trang_thai, ngay_nhap, gia_nhap, serial_number
                    FROM photocopy_machines
                    WHERE trang_thai = 'Trong Kho'
                    ORDER BY ngay_nhap DESC
                    LIMIT %s OFFSET %s
                """
                self.cursor.execute(query, (limit, offset))
                self.machines_cache = [list(item) for item in self.cursor.fetchall()]
                self.last_fetch_time = current_time
                self.cache_changed['machines'] = False
                print(
                    f"Đã làm mới danh sách máy photocopy có sẵn: {len(self.machines_cache)} mục (offset={offset}, limit={limit})")
            except mysql.connector.Error as err:
                logging.error(f"Error fetching available photocopy machines: {err}")
                sg.popup_error(f"Lỗi khi lấy danh sách máy photocopy có sẵn: {err}")
                self.machines_cache = []
        return self.machines_cache if self.machines_cache is not None else []

    def return_photocopy_machine(self, machine_id, return_date, return_counter, return_customer_name,
                                 return_customer_phone):
        if return_counter < 0:
            sg.popup_error("Số counter trả phải lớn hơn hoặc bằng 0!")
            return False
        try:
            self.cursor.execute("SELECT trang_thai, ten_may FROM photocopy_machines WHERE id=%s", (machine_id,))
            machine = self.cursor.fetchone()
            if not machine:
                sg.popup_error("Máy không tồn tại!")
                return False
            if machine[0] != 'Đang Cho Thuê':
                sg.popup_error(f"Máy {machine[1]} không đang được cho thuê! Trạng thái: {machine[0]}")
                return False

            self.cursor.execute(
                "UPDATE photocopy_machines SET trang_thai='Trong Kho', so_counter=%s WHERE id=%s",
                (return_counter, machine_id)
            )
            self.cursor.execute(
                "INSERT INTO counter_history (machine_id, counter_value, record_date) VALUES (%s, %s, %s)",
                (machine_id, return_counter, return_date)
            )
            self.cursor.execute(
                "UPDATE rental_history SET return_date=%s, return_counter=%s, return_customer_name=%s, return_customer_phone=%s "
                "WHERE machine_id=%s AND return_date IS NULL",
                (return_date, return_counter, return_customer_name, return_customer_phone, machine_id)
            )
            self.conn.commit()
            self.cache_changed['machines'] = True
            self.cache_changed['rentals'] = True
            self.cache_changed['counter'] = True
            print(f"Đã trả máy photocopy ID {machine_id} vào kho, counter mới: {return_counter}")
            return True
        except mysql.connector.Error as err:
            logging.error(f"Error returning machine ID {machine_id}: {err}")
            sg.popup_error(f"Lỗi khi trả máy photocopy: {err}")
            return False

    def fetch_rental_history(self, force_refresh=False):
        current_time = time.time()
        if force_refresh or self.rental_cache is None or (current_time - self.last_fetch_time > self.cache_timeout) or \
                self.cache_changed['rentals']:
            try:
                query = """
                    SELECT m.ten_may, r.customer_name, r.customer_phone, r.start_date, r.end_date, r.rental_price,
                           (r.rental_price * DATEDIFF(r.end_date, r.start_date)) as profit,
                           r.return_date, r.return_counter, r.return_customer_name, r.return_customer_phone
                    FROM rental_history r 
                    LEFT JOIN photocopy_machines m ON r.machine_id = m.id
                    ORDER BY r.start_date DESC
                    LIMIT 10
                """
                self.cursor.execute(query)
                self.rental_cache = [list(item) for item in self.cursor.fetchall()]
                self.last_fetch_time = current_time
                self.cache_changed['rentals'] = False
                print(f"Đã làm mới lịch sử cho thuê máy photocopy: {len(self.rental_cache)} mục")
            except mysql.connector.Error as err:
                logging.error(f"Error fetching rental history: {err}")
                sg.popup_error(f"Lỗi khi lấy lịch sử cho thuê máy photocopy: {err}")
                self.rental_cache = []
        return self.rental_cache if self.rental_cache is not None else []

    def backup_all_data(self, backup_path):
        try:
            tables = {
                'vat_tu': self.fetch_all_items(offset=0, limit=1000),
                'sales_history': self.fetch_sales_history(),
                'import_history': self.fetch_import_history(),
                'photocopy_machines': self.fetch_all_photocopy_machines(offset=0, limit=1000),
                'photocopy_sales_history': self.fetch_photocopy_sales_history(),
                'rental_history': self.fetch_rental_history(),
                'maintenance_history': self.fetch_maintenance_history(),
                'counter_history': [(r[0], r[1]) for r in self.fetch_counter_history(0, force_refresh=True)]
                # Lấy tất cả counter
            }
            with pd.ExcelWriter(backup_path, engine='openpyxl') as writer:
                has_data = False
                for table_name, data in tables.items():
                    if data:
                        has_data = True
                        for row in data:
                            for i in range(len(row)):
                                if row[i] is None:
                                    row[i] = ""
                        if table_name == 'vat_tu':
                            df = pd.DataFrame(data, columns=['ID', 'Loại', 'Nhà Cung Cấp', 'Số Lượng Tồn', 'Giá Nhập'])
                        elif table_name == 'sales_history':
                            df = pd.DataFrame(data, columns=['Loại', 'Số Lượng', 'Ngày Bán', 'Giá Bán', 'Doanh Thu',
                                                             'Tên Khách Hàng', 'SĐT'])
                        elif table_name == 'import_history':
                            df = pd.DataFrame(data, columns=['Loại', 'Số Lượng', 'Ngày Nhập', 'Giá Nhập'])
                        elif table_name == 'photocopy_machines':
                            df = pd.DataFrame(data, columns=['ID', 'Loại Máy', 'Tên Máy', 'Số Counter', 'Trạng Thái',
                                                             'Ngày Nhập', 'Giá Nhập', 'Số Serial'])
                        elif table_name == 'photocopy_sales_history':
                            df = pd.DataFrame(data,
                                              columns=['Tên Máy', 'Ngày Bán', 'Giá Bán', 'Lợi Nhuận', 'Tên Khách Hàng',
                                                       'SĐT'])
                        elif table_name == 'rental_history':
                            df = pd.DataFrame(data, columns=['Tên Máy', 'Tên Khách Hàng', 'SĐT', 'Ngày Bắt Đầu',
                                                             'Ngày Kết Thúc', 'Giá Thuê', 'Lợi Nhuận', 'Ngày Trả',
                                                             'Counter Trả', 'Khách Hàng Trả', 'SĐT Trả'])
                        elif table_name == 'maintenance_history':
                            df = pd.DataFrame(data, columns=['Tên Máy', 'Ngày Bảo Trì', 'Mô Tả', 'Chi Phí'])
                        elif table_name == 'counter_history':
                            df = pd.DataFrame(data, columns=['Ngày Ghi', 'Counter'])
                        df.to_excel(writer, sheet_name=table_name, index=False)
                        print(f"Debug - Đã backup bảng {table_name} với {len(data)} dòng")

                if not has_data:
                    df = pd.DataFrame([["Không có dữ liệu để backup"]], columns=["Thông báo"])
                    df.to_excel(writer, sheet_name='Trống', index=False)
                    print("Debug - Không có dữ liệu, tạo sheet mặc định 'Trống'")

            print(f"Đã backup dữ liệu vào: {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Error backing up data to {backup_path}: {e}")
            sg.popup_error(f"Lỗi khi backup dữ liệu: {e}")
            return False

    def clear_all_data(self):
        try:
            tables = [
                'counter_history', 'maintenance_history', 'rental_history',
                'photocopy_sales_history', 'import_history', 'sales_history',
                'photocopy_machines', 'vat_tu'
            ]
            for table in tables:
                print(f"Debug - Bắt đầu xóa bảng: {table}")
                self.cursor.execute(f"DELETE FROM {table}")
                self.cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
                print(f"Debug - Đã xóa bảng: {table}")
            self.conn.commit()
            self.items_cache = None
            self.sales_cache = None
            self.import_cache = None
            self.machines_cache = None
            self.photocopy_sales_cache = None
            self.rental_cache = None
            self.maintenance_cache = None
            self.counter_cache = None
            self.cache_changed = {key: True for key in self.cache_changed}
            print("Đã xóa toàn bộ dữ liệu trong tất cả các bảng (trừ users) và làm mới cache!")
            return True
        except mysql.connector.Error as err:
            logging.error(f"Error clearing all data: {err}")
            sg.popup_error(f"Lỗi khi xóa dữ liệu: {err}")
            print(f"Lỗi khi xóa dữ liệu: {err}")
            return False

    def delete_item(self, item_id):
        try:
            self.cursor.execute("DELETE FROM vat_tu WHERE id=%s", (item_id,))
            self.conn.commit()
            self.cache_changed['items'] = True
            print(f"Đã xóa vật tư ID {item_id}")
            return True
        except mysql.connector.Error as err:
            logging.error(f"Error deleting item ID {item_id}: {err}")
            sg.popup_error(f"Lỗi khi xóa vật tư: {err}")
            return False

    def fetch_sales_history(self, force_refresh=False):
        current_time = time.time()
        if force_refresh or self.sales_cache is None or (current_time - self.last_fetch_time > self.cache_timeout) or \
                self.cache_changed['sales']:
            try:
                query = """
                    SELECT v.loai, s.quantity_sold, s.sale_date, s.selling_price, 
                           (s.selling_price * s.quantity_sold) as revenue,
                           s.customer_name, s.customer_phone
                    FROM sales_history s 
                    LEFT JOIN vat_tu v ON s.item_id = v.id
                    ORDER BY s.sale_date DESC
                    LIMIT 10
                """
                self.cursor.execute(query)
                self.sales_cache = [list(item) for item in self.cursor.fetchall()]
                self.last_fetch_time = current_time
                self.cache_changed['sales'] = False
                print(f"Đã làm mới lịch sử bán hàng: {len(self.sales_cache)} mục")
            except mysql.connector.Error as err:
                logging.error(f"Error fetching sales history: {err}")
                sg.popup_error(f"Lỗi khi lấy lịch sử bán hàng: {err}")
                return []
        return self.sales_cache if self.sales_cache is not None else []

    def fetch_import_history(self, force_refresh=False):
        current_time = time.time()
        if force_refresh or self.import_cache is None or (current_time - self.last_fetch_time > self.cache_timeout) or \
                self.cache_changed['imports']:
            try:
                query = """
                    SELECT v.loai, i.quantity_imported, i.import_date, i.import_price
                    FROM import_history i 
                    LEFT JOIN vat_tu v ON i.item_id = v.id
                    ORDER BY i.import_date DESC
                    LIMIT 10
                """
                self.cursor.execute(query)
                self.import_cache = [list(item) for item in self.cursor.fetchall()]
                self.last_fetch_time = current_time
                self.cache_changed['imports'] = False
                print(f"Đã làm mới lịch sử nhập hàng: {len(self.import_cache)} mục")
            except mysql.connector.Error as err:
                logging.error(f"Error fetching import history: {err}")
                sg.popup_error(f"Lỗi khi lấy lịch sử nhập hàng: {err}")
                return []
        return self.import_cache if self.import_cache is not None else []

    def sell_item(self, item_id, quantity_sold, selling_price, customer_name, customer_phone):
        if quantity_sold <= 0 or selling_price < 0:
            sg.popup_error("Số lượng bán và giá bán phải lớn hơn 0!")
            return False
        try:
            self.cursor.execute("SELECT so_luong_ton FROM vat_tu WHERE id=%s", (item_id,))
            result = self.cursor.fetchone()
            if result is None:
                sg.popup_error("Vật tư không tồn tại!")
                return False
            current_quantity = result[0]
            if current_quantity < quantity_sold:
                sg.popup_error("Số lượng tồn kho không đủ để bán!")
                return False

            new_quantity = current_quantity - quantity_sold
            self.cursor.execute("UPDATE vat_tu SET so_luong_ton=%s WHERE id=%s", (new_quantity, item_id))
            self.cursor.execute(
                "INSERT INTO sales_history (item_id, quantity_sold, sale_date, selling_price, customer_name, customer_phone) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (item_id, quantity_sold, date.today(), selling_price, customer_name, customer_phone)
            )
            self.conn.commit()
            self.cache_changed['items'] = True
            self.cache_changed['sales'] = True
            print(f"Đã bán vật tư ID {item_id}: {quantity_sold} đơn vị")
            return True
        except mysql.connector.Error as err:
            logging.error(f"Error selling item ID {item_id}: {err}")
            sg.popup_error(f"Lỗi khi bán hàng: {err}")
            return False

    def import_item(self, loai, nha_cung_cap, quantity_imported, import_price=None):
        if quantity_imported <= 0:
            sg.popup_error("Số lượng nhập phải lớn hơn 0!")
            return None
        if import_price is not None and import_price < 0:
            sg.popup_error("Giá nhập không được âm!")
            return None
        try:
            self.cursor.execute("SELECT id, so_luong_ton FROM vat_tu WHERE loai=%s AND nha_cung_cap=%s",
                                (loai, nha_cung_cap))
            result = self.cursor.fetchone()

            if result:
                item_id, current_quantity = result
                new_quantity = current_quantity + quantity_imported
                if import_price is None:
                    self.cursor.execute(
                        "SELECT import_price FROM import_history WHERE item_id=%s ORDER BY import_date DESC LIMIT 1",
                        (item_id,)
                    )
                    last_price = self.cursor.fetchone()
                    import_price = last_price[0] if last_price else 0
                self.cursor.execute(
                    "UPDATE vat_tu SET so_luong_ton=%s WHERE id=%s",
                    (new_quantity, item_id)
                )
            else:
                if import_price is None:
                    sg.popup_error("Vật tư mới cần cung cấp giá nhập hàng!")
                    return None
                self.cursor.execute(
                    "INSERT INTO vat_tu (loai, nha_cung_cap, so_luong_ton) VALUES (%s, %s, %s)",
                    (loai, nha_cung_cap, quantity_imported)
                )
                self.cursor.execute("SELECT LAST_INSERT_ID()")
                item_id = self.cursor.fetchone()[0]

            self.cursor.execute(
                "INSERT INTO import_history (item_id, quantity_imported, import_date, import_price) VALUES (%s, %s, %s, %s)",
                (item_id, quantity_imported, date.today(), import_price)
            )
            self.conn.commit()
            self.cache_changed['items'] = True
            self.cache_changed['imports'] = True
            print(f"Đã nhập hàng cho vật tư ID {item_id}: {quantity_imported} đơn vị")
            return item_id
        except mysql.connector.Error as err:
            logging.error(f"Error importing item {loai}: {err}")
            sg.popup_error(f"Lỗi khi nhập hàng: {err}")
            return None

    def sell_photocopy_machine(self, machine_id, quantity, selling_price, customer_name, customer_phone):
        if quantity <= 0 or selling_price < 0:
            sg.popup_error("Số lượng bán và giá bán phải lớn hơn 0!")
            return False
        try:
            self.cursor.execute("SELECT trang_thai, ten_may, gia_nhap FROM photocopy_machines WHERE id=%s",
                                (machine_id,))
            machine = self.cursor.fetchone()
            if not machine:
                sg.popup_error("Máy không tồn tại!")
                return False
            if machine[0] != 'Trong Kho':
                sg.popup_error(f"Máy {machine[1]} không trong kho để bán! Trạng thái: {machine[0]}")
                return False
            if quantity > 1:
                sg.popup_error("Hệ thống hiện chỉ hỗ trợ bán 1 máy mỗi lần!")
                return False

            machine_name = machine[1]
            gia_nhap = machine[2]
            self.cursor.execute(
                "INSERT INTO photocopy_sales_history (machine_id, machine_name, sale_date, selling_price, gia_nhap, customer_name, customer_phone) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (machine_id, machine_name, date.today(), selling_price, gia_nhap, customer_name, customer_phone)
            )
            self.cursor.execute("DELETE FROM photocopy_machines WHERE id=%s", (machine_id,))
            self.conn.commit()
            self.cache_changed['machines'] = True
            self.cache_changed['photocopy_sales'] = True
            print(f"Đã bán và xóa máy photocopy ID {machine_id} cho {customer_name}")
            return True
        except mysql.connector.Error as err:
            logging.error(f"Error selling machine ID {machine_id}: {err}")
            sg.popup_error(f"Lỗi khi bán máy photocopy: {err}")
            return False

    def fetch_photocopy_sales_history(self, force_refresh=False):
        current_time = time.time()
        if force_refresh or self.photocopy_sales_cache is None or (
                current_time - self.last_fetch_time > self.cache_timeout) or self.cache_changed['photocopy_sales']:
            try:
                query = """
                    SELECT machine_name, sale_date, selling_price, (selling_price - gia_nhap) as profit, customer_name, customer_phone
                    FROM photocopy_sales_history
                    ORDER BY sale_date DESC
                    LIMIT 10
                """
                self.cursor.execute(query)
                self.photocopy_sales_cache = [list(item) for item in self.cursor.fetchall()]
                self.last_fetch_time = current_time
                self.cache_changed['photocopy_sales'] = False
                print(f"Đã làm mới lịch sử bán máy photocopy: {len(self.photocopy_sales_cache)} mục")
            except mysql.connector.Error as err:
                logging.error(f"Error fetching photocopy sales history: {err}")
                sg.popup_error(f"Lỗi khi lấy lịch sử bán máy photocopy: {err}")
                return []
        return self.photocopy_sales_cache if self.photocopy_sales_cache is not None else []

    def rent_photocopy_machine(self, machine_id, customer_name, customer_phone, start_date, end_date, rental_price):
        if rental_price < 0:
            sg.popup_error("Giá thuê phải lớn hơn hoặc bằng 0!")
            return False
        try:
            self.cursor.execute("SELECT trang_thai, ten_may FROM photocopy_machines WHERE id=%s", (machine_id,))
            machine = self.cursor.fetchone()
            if not machine:
                sg.popup_error("Máy không tồn tại!")
                return False
            if machine[0] != 'Trong Kho':
                sg.popup_error(f"Máy {machine[1]} không trong kho để cho thuê! Trạng thái: {machine[0]}")
                return False

            self.cursor.execute("UPDATE photocopy_machines SET trang_thai='Đang Cho Thuê' WHERE id=%s", (machine_id,))
            self.cursor.execute(
                "INSERT INTO rental_history (machine_id, customer_name, customer_phone, start_date, end_date, rental_price) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (machine_id, customer_name, customer_phone, start_date, end_date, rental_price)
            )
            self.conn.commit()
            self.cache_changed['machines'] = True
            self.cache_changed['rentals'] = True
            print(f"Đã cho thuê máy photocopy ID {machine_id} cho {customer_name}")
            return True
        except mysql.connector.Error as err:
            logging.error(f"Error renting machine ID {machine_id}: {err}")
            sg.popup_error(f"Lỗi khi cho thuê máy photocopy: {err}")
            return False

    def add_maintenance_record(self, machine_id, description, cost):
        if cost < 0:
            sg.popup_error("Chi phí bảo trì không được âm!")
            return False
        try:
            self.cursor.execute(
                "INSERT INTO maintenance_history (machine_id, maintenance_date, description, cost) "
                "VALUES (%s, %s, %s, %s)",
                (machine_id, date.today(), description, cost)
            )
            self.cursor.execute(
                "UPDATE photocopy_machines SET last_maintenance_date = %s WHERE id = %s",
                (date.today(), machine_id)
            )
            self.conn.commit()
            self.cache_changed['maintenance'] = True
            self.cache_changed['machines'] = True
            print(f"Đã thêm bảo trì cho máy ID {machine_id}")
            return True
        except mysql.connector.Error as err:
            logging.error(f"Error adding maintenance for machine ID {machine_id}: {err}")
            sg.popup_error(f"Lỗi khi thêm bảo trì: {err}")
            return False

    def fetch_maintenance_history(self, machine_id=None, force_refresh=False):
        current_time = time.time()
        if force_refresh or self.maintenance_cache is None or (
                current_time - self.last_fetch_time > self.cache_timeout) or self.cache_changed['maintenance']:
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
                    query += " ORDER BY mh.maintenance_date DESC LIMIT 10"
                    self.cursor.execute(query)
                self.maintenance_cache = [list(row) for row in self.cursor.fetchall()]
                self.last_fetch_time = current_time
                self.cache_changed['maintenance'] = False
                print(f"Đã làm mới lịch sử bảo trì: {len(self.maintenance_cache)} mục")
            except mysql.connector.Error as err:
                logging.error(f"Error fetching maintenance history: {err}")
                sg.popup_error(f"Lỗi khi lấy lịch sử bảo trì: {err}")
                return []
        if machine_id:
            return [row for row in self.maintenance_cache if row[0] == machine_id]
        return self.maintenance_cache if self.maintenance_cache is not None else []

    def delete_photocopy_machine(self, machine_id):
        try:
            self.cursor.execute("SELECT trang_thai, ten_may FROM photocopy_machines WHERE id=%s", (machine_id,))
            machine = self.cursor.fetchone()
            if not machine:
                sg.popup_error(f"Máy với ID {machine_id} không tồn tại!")
                return False
            if machine[0] == 'Đang Cho Thuê':
                sg.popup_error(f"Máy {machine[1]} đang được cho thuê, không thể xóa!")
                return False

            self.cursor.execute("DELETE FROM photocopy_machines WHERE id=%s", (machine_id,))
            self.conn.commit()
            self.cache_changed['machines'] = True
            print(f"Đã xóa máy photocopy ID {machine_id}")
            return True
        except mysql.connector.Error as err:
            logging.error(f"Error deleting photocopy machine ID {machine_id}: {err}")
            sg.popup_error(f"Lỗi khi xóa máy photocopy: {err}")
            return False

    def check_maintenance_due(self):
        """Kiểm tra các máy cần bảo trì"""
        try:
            query = """
                SELECT id, ten_may, last_maintenance_date, maintenance_interval
                FROM photocopy_machines
                WHERE last_maintenance_date IS NOT NULL
                AND DATE_ADD(last_maintenance_date, INTERVAL maintenance_interval DAY) <= CURDATE()
            """
            self.cursor.execute(query)
            return [list(row) for row in self.cursor.fetchall()]
        except mysql.connector.Error as err:
            logging.error(f"Error checking maintenance due: {err}")
            return []

    def export_to_excel(self, file_path, is_history=False, is_photocopy=False):
        try:
            if is_photocopy:
                if is_history:
                    if 'rental' in file_path.lower():
                        data = self.fetch_rental_history()
                        if not data:
                            sg.popup_error("Không có dữ liệu lịch sử thuê máy photocopy để xuất!", title="Thông báo")
                            return False
                        for row in data:
                            for i in range(len(row)):
                                if row[i] is None:
                                    row[i] = ""
                        df = pd.DataFrame(data,
                                          columns=['Tên Máy', 'Tên Khách Hàng', 'SĐT', 'Ngày Bắt Đầu', 'Ngày Kết Thúc',
                                                   'Giá Thuê', 'Lợi Nhuận', 'Ngày Trả', 'Counter Trả', 'Khách Hàng Trả',
                                                   'SĐT Trả'])
                    else:
                        data = self.fetch_photocopy_sales_history()
                        if not data:
                            sg.popup_error("Không có dữ liệu lịch sử bán máy photocopy để xuất!", title="Thông báo")
                            return False
                        for row in data:
                            for i in range(len(row)):
                                if row[i] is None:
                                    row[i] = ""
                        df = pd.DataFrame(data,
                                          columns=['Tên Máy', 'Ngày Bán', 'Giá Bán', 'Lợi Nhuận', 'Tên Khách Hàng',
                                                   'SĐT'])
                else:
                    data = self.fetch_all_photocopy_machines(offset=0, limit=1000, force_refresh=True)
                    if not data:
                        sg.popup_error("Không có dữ liệu máy photocopy để xuất!", title="Thông báo")
                        return False
                    for row in data:
                        for i in range(len(row)):
                            if row[i] is None:
                                row[i] = ""
                    df = pd.DataFrame(data,
                                      columns=['ID', 'Loại Máy', 'Tên Máy', 'Số Counter', 'Trạng Thái', 'Ngày Nhập',
                                               'Giá Nhập', 'Số Serial'])
            else:
                if is_history:
                    data = self.fetch_sales_history()
                    if not data:
                        sg.popup_error("Không có dữ liệu lịch sử bán hàng để xuất!", title="Thông báo")
                        return False
                    for row in data:
                        for i in range(len(row)):
                            if row[i] is None:
                                row[i] = ""
                    df = pd.DataFrame(data,
                                      columns=['Loại', 'Số Lượng', 'Ngày Bán', 'Giá Bán', 'Doanh Thu', 'Tên Khách Hàng',
                                               'SĐT'])
                else:
                    data = self.fetch_all_items(offset=0, limit=1000, force_refresh=True)
                    if not data:
                        sg.popup_error("Không có dữ liệu vật tư để xuất!", title="Thông báo")
                        return False
                    for row in data:
                        for i in range(len(row)):
                            if row[i] is None:
                                row[i] = ""
                    df = pd.DataFrame(data, columns=['ID', 'Loại', 'Nhà Cung Cấp', 'Số Lượng Tồn', 'Giá Nhập'])

            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Dữ liệu', index=False)
            print(f"Đã xuất Excel: {file_path}")
            sg.popup(f"Đã xuất dữ liệu thành công vào: {file_path}", title="Thành công")
            return True
        except Exception as e:
            logging.error(f"Error exporting to Excel {file_path}: {e}")
            sg.popup_error(f"Lỗi xuất Excel: {e}")
            return False

    def check_low_inventory(self):
        try:
            items = self.fetch_all_items(offset=0, limit=1000)
            low_items = [item for item in items if item[3] < 10]
            print(f"Cảnh báo tồn kho thấp: {len(low_items)} mục")
            return low_items
        except mysql.connector.Error as err:
            logging.error(f"Error checking low inventory: {err}")
            sg.popup_error(f"Lỗi khi kiểm tra tồn kho: {err}")
            return []

    def get_sales_stats(self):
        try:
            self.cursor.execute("SELECT SUM(quantity_sold), SUM(selling_price * quantity_sold) FROM sales_history")
            result = self.cursor.fetchone()
            return {"total_quantity": result[0] or 0, "total_revenue": result[1] or 0}
        except mysql.connector.Error as err:
            logging.error(f"Error getting sales stats: {err}")
            sg.popup_error(f"Lỗi khi lấy thống kê bán hàng: {err}")
            return {"total_quantity": 0, "total_revenue": 0}

    def get_detailed_sales_stats(self):
        try:
            query = """
                SELECT v.loai, SUM(s.quantity_sold), SUM(s.selling_price * s.quantity_sold),
                       SUM((s.selling_price - COALESCE(i.import_price, 0)) * s.quantity_sold)
                FROM sales_history s
                LEFT JOIN vat_tu v ON s.item_id = v.id
                LEFT JOIN (
                    SELECT item_id, import_price
                    FROM import_history
                    WHERE (item_id, import_date) IN (
                        SELECT item_id, MAX(import_date)
                        FROM import_history
                        GROUP BY item_id
                    )
                ) i ON s.item_id = i.item_id
                GROUP BY v.loai
            """
            self.cursor.execute(query)
            return [list(row) for row in self.cursor.fetchall()]
        except mysql.connector.Error as err:
            logging.error(f"Error getting detailed sales stats: {err}")
            sg.popup_error(f"Lỗi khi lấy thống kê chi tiết: {err}")
            return []

    def get_photocopy_rental_stats(self):
        try:
            self.cursor.execute(
                "SELECT COUNT(id), SUM(rental_price * DATEDIFF(end_date, start_date)) FROM rental_history")
            result = self.cursor.fetchone()
            return {"total_rentals": result[0] or 0, "total_revenue": result[1] or 0}
        except mysql.connector.Error as err:
            logging.error(f"Error getting photocopy rental stats: {err}")
            sg.popup_error(f"Lỗi khi lấy thống kê thuê máy: {err}")
            return {"total_rentals": 0, "total_revenue": 0}

    def get_photocopy_sales_stats(self):
        try:
            self.cursor.execute("SELECT COUNT(id), SUM(selling_price) FROM photocopy_sales_history")
            result = self.cursor.fetchone()
            return {"total_sales": result[0] or 0, "total_revenue": result[1] or 0}
        except mysql.connector.Error as err:
            logging.error(f"Error getting photocopy sales stats: {err}")
            sg.popup_error(f"Lỗi khi lấy thống kê bán máy: {err}")
            return {"total_sales": 0, "total_revenue": 0}

    def get_detailed_photocopy_stats(self):
        try:
            query = """
                SELECT 'Bán Máy' AS type, 
                       COUNT(id) AS total_sales, 
                       SUM(selling_price) AS total_revenue,
                       SUM(selling_price - COALESCE(gia_nhap, 0)) AS total_profit
                FROM photocopy_sales_history
                UNION
                SELECT 'Thuê Máy', 
                       COUNT(id), 
                       SUM(rental_price * DATEDIFF(end_date, start_date)),
                       SUM(rental_price * DATEDIFF(end_date, start_date))
                FROM rental_history
            """
            self.cursor.execute(query)
            stats = [list(row) for row in self.cursor.fetchall()]
            print(f"Thống kê chi tiết: {stats}")
            return stats
        except mysql.connector.Error as err:
            logging.error(f"Error getting detailed photocopy stats: {err}")
            sg.popup_error(f"Lỗi khi lấy thống kê chi tiết máy: {err}")
            return []