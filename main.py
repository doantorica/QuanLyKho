import mysql.connector
import PySimpleGUI as sg
from gui_layout import create_layout
from gui_events import handle_events
from gui_refresh import (refresh_items_table, refresh_sales_table, refresh_import_table,
                         refresh_photocopy_table, refresh_rental_table, refresh_maintenance_table,
                         refresh_photocopy_sales_table)
from database import InventoryManager, DB_CONFIG
import bcrypt
import configparser
import os
from cryptography.fernet import Fernet
import base64

# File lưu cấu hình
CONFIG_FILE = "config.ini"
KEY_FILE = "secret.key"  # File lưu khóa mã hóa


# Tạo hoặc đọc khóa mã hóa
def get_encryption_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as key_file:
            key_file.write(key)
        return key


# Mã hóa dữ liệu
def encrypt_data(data, key):
    fernet = Fernet(key)
    return fernet.encrypt(data.encode()).decode()


# Giải mã dữ liệu
def decrypt_data(encrypted_data, key):
    fernet = Fernet(key)
    try:
        return fernet.decrypt(encrypted_data.encode()).decode()
    except:
        return ""


# Đọc cấu hình
def load_config():
    config = configparser.ConfigParser()
    key = get_encryption_key()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        if 'Login' in config:
            username = config['Login'].get('username', 'admin')
            encrypted_password = config['Login'].get('password', '')
            password = decrypt_data(encrypted_password, key) if encrypted_password else ''
            return username, password
    return 'admin', ''  # Mặc định username là "admin", password rỗng nếu chưa lưu


# Lưu cấu hình
def save_config(username, password):
    config = configparser.ConfigParser()
    key = get_encryption_key()
    encrypted_password = encrypt_data(password, key) if password else ''
    config['Login'] = {
        'username': username,
        'password': encrypted_password
    }
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def show_login_window():
    sg.theme('LightGrey1')
    default_username, default_password = load_config()
    layout = [
        [sg.Text("Đăng Nhập", font=('Helvetica', 16, 'bold'), justification='center')],
        [sg.Text("Tên đăng nhập:", size=(15, 1)), sg.Input(default_username, key='username', size=(20, 1))],
        [sg.Text("Mật khẩu:", size=(15, 1)),
         sg.Input(default_password, key='password', password_char='*', size=(20, 1))],
        [sg.Checkbox("Lưu mật khẩu", key='save_password', default=bool(default_password))],
        [sg.Button("Đăng Nhập", size=(10, 1)), sg.Button("Bỏ Qua", size=(10, 1))]
    ]
    window = sg.Window("Đăng Nhập", layout, size=(300, 200), finalize=True)
    role = None
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Bỏ Qua"):
            window.close()
            return 'user'
        elif event == "Đăng Nhập":
            try:
                conn = mysql.connector.connect(**DB_CONFIG)
                print("Debug - Database connection successful")
                inventory_manager = InventoryManager(conn)
                role = inventory_manager.authenticate_user(values['username'], values['password'])
                if role:
                    print(f"Debug - Login successful, role: {role}")
                    if values['save_password']:
                        save_config(values['username'], values['password'])
                    else:
                        save_config(values['username'], '')
                    window.close()
                    return role
                else:
                    sg.popup_error("Tên đăng nhập hoặc mật khẩu không đúng!")
            except mysql.connector.Error as err:
                sg.popup_error(f"Lỗi kết nối cơ sở dữ liệu: {err}")
                break
    window.close()
    return None


def show_change_password_window(inventory_manager, current_username):
    layout = [
        [sg.Text("Đổi Mật Khẩu", font=('Helvetica', 16, 'bold'), justification='center')],
        [sg.Text("Mật khẩu cũ:", size=(15, 1)), sg.Input(key='old_password', password_char='*', size=(20, 1))],
        [sg.Text("Mật khẩu mới:", size=(15, 1)), sg.Input(key='new_password', password_char='*', size=(20, 1))],
        [sg.Text("Xác nhận mật khẩu mới:", size=(15, 1)),
         sg.Input(key='confirm_password', password_char='*', size=(20, 1))],
        [sg.Button("Xác Nhận", size=(10, 1)), sg.Button("Hủy", size=(10, 1))]
    ]
    window = sg.Window("Đổi Mật Khẩu", layout, size=(350, 250), finalize=True)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Hủy"):
            break
        elif event == "Xác Nhận":
            old_password = values['old_password']
            new_password = values['new_password']
            confirm_password = values['confirm_password']

            if not inventory_manager.authenticate_user(current_username, old_password):
                sg.popup_error("Mật khẩu cũ không đúng!")
                continue

            if new_password != confirm_password:
                sg.popup_error("Mật khẩu mới và xác nhận không khớp!")
                continue
            if len(new_password) < 6:
                sg.popup_error("Mật khẩu mới phải dài ít nhất 6 ký tự!")
                continue

            try:
                new_hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                inventory_manager.cursor.execute(
                    "UPDATE users SET password = %s WHERE username = %s",
                    (new_hashed_password, current_username)
                )
                inventory_manager.conn.commit()
                sg.popup("Đổi mật khẩu thành công!")
                save_config(current_username, new_password)
                break
            except mysql.connector.Error as err:
                sg.popup_error(f"Lỗi khi đổi mật khẩu: {err}")
                break

    window.close()


def main():
    role = show_login_window()
    if role is None:
        return

    conn = mysql.connector.connect(**DB_CONFIG)
    inventory_manager = InventoryManager(conn)
    inventory_manager.setup_database()

    layout = create_layout()
    control_column = [
        [sg.Button("Thống Kê", size=(15, 1), font=('Helvetica', 10), button_color=('white', '#6c757d'))],
        [sg.Button("Xuất Excel", size=(15, 1), font=('Helvetica', 10), button_color=('white', '#6c757d'))],
        [sg.Button("Xuất Lịch Sử", size=(15, 1), font=('Helvetica', 10), button_color=('white', '#6c757d'))],
        [sg.Button("Xóa Toàn Bộ Dữ Liệu", size=(15, 1), font=('Helvetica', 10), button_color=('white', '#dc3545'))],
        [sg.Button("Làm Mới", size=(15, 1), font=('Helvetica', 10), button_color=('white', '#17a2b8'))],
    ]
    if role == 'admin':
        control_column.insert(0, [
            sg.Button("Đổi Mật Khẩu", size=(15, 1), font=('Helvetica', 10), button_color=('white', '#007bff'))])
    control_column.append([sg.Button("Thoát", size=(15, 1), font=('Helvetica', 10), button_color=('white', '#dc3545'))])
    layout[1][0] = sg.Column(control_column, vertical_alignment='top', pad=(10, 10))

    window = sg.Window("Quản Lý Kho", layout, size=(1000, 800), resizable=True, finalize=True)

    vat_tu_page = 1
    photocopy_page = 1
    current_tab = window.Element('TabGroup').Get()
    current_username = "admin" if role == "admin" else None

    if current_tab == 'Quản Lý Vật Tư':
        refresh_items_table(window, inventory_manager, vat_tu_page)
        refresh_sales_table(window, inventory_manager)
        refresh_import_table(window, inventory_manager)
    else:
        refresh_photocopy_table(window, inventory_manager, photocopy_page)
        refresh_rental_table(window, inventory_manager)
        refresh_maintenance_table(window, inventory_manager)
        refresh_photocopy_sales_table(window, inventory_manager)

    current_item_id = None
    selected_machine_id = None

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "Thoát":
            break
        elif event == "Đổi Mật Khẩu" and role == 'admin':
            show_change_password_window(inventory_manager, current_username)
        else:
            current_item_id, selected_machine_id, vat_tu_page, photocopy_page = handle_events(
                window, event, values, inventory_manager, current_item_id, selected_machine_id, vat_tu_page,
                photocopy_page, role
            )

    window.close()
    conn.close()


if __name__ == "__main__":
    main()