import mysql.connector
import PySimpleGUI as sg
from gui_layout import create_layout
from gui_events import handle_events
from gui_refresh import (refresh_items_table, refresh_sales_table, refresh_import_table,
                         refresh_photocopy_table, refresh_rental_table, refresh_maintenance_table,
                         refresh_photocopy_sales_table)
from database import InventoryManager, DB_CONFIG

def show_login_window():
    sg.theme('LightGrey1')
    layout = [
        [sg.Text("Đăng Nhập", font=('Helvetica', 16, 'bold'), justification='center')],
        [sg.Text("Tên đăng nhập:", size=(15, 1)), sg.Input(key='username', size=(20, 1))],
        [sg.Text("Mật khẩu:", size=(15, 1)), sg.Input(key='password', password_char='*', size=(20, 1))],
        [sg.Button("Đăng Nhập", size=(10, 1)), sg.Button("Bỏ Qua", size=(10, 1))]
    ]
    window = sg.Window("Đăng Nhập", layout, size=(300, 200), finalize=True)
    role = None
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == "Đăng Nhập":
            try:
                conn = mysql.connector.connect(**DB_CONFIG)
                inventory_manager = InventoryManager(conn)
                role = inventory_manager.authenticate_user(values['username'], values['password'])
                if role:
                    window.close()
                    return role
                else:
                    sg.popup_error("Tên đăng nhập hoặc mật khẩu không đúng!")
            except mysql.connector.Error as err:
                sg.popup_error(f"Lỗi kết nối cơ sở dữ liệu: {err}")
                break
        elif event == "Bỏ Qua":
            window.close()
            return 'user'  # Vai trò mặc định khi bỏ qua
    window.close()
    return None

def main():
    role = show_login_window()
    if role is None:  # Người dùng đóng cửa sổ đăng nhập
        return

    conn = mysql.connector.connect(**DB_CONFIG)
    inventory_manager = InventoryManager(conn)
    inventory_manager.setup_database()

    layout = create_layout()
    window = sg.Window("Quản Lý Kho", layout, size=(1000, 800), resizable=True, finalize=True)

    vat_tu_page = 1
    photocopy_page = 1
    current_tab = window.Element('TabGroup').Get()

    # Làm mới dữ liệu khi khởi động
    inventory_manager.items_cache = None
    inventory_manager.sales_cache = None
    inventory_manager.import_cache = None
    inventory_manager.machines_cache = None
    inventory_manager.photocopy_sales_cache = None
    inventory_manager.rental_cache = None
    inventory_manager.maintenance_cache = None

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
        # Truyền thêm tham số role vào handle_events
        current_item_id, selected_machine_id, vat_tu_page, photocopy_page = handle_events(
            window, event, values, inventory_manager, current_item_id, selected_machine_id, vat_tu_page, photocopy_page, role
        )

    window.close()
    conn.close()

if __name__ == "__main__":
    main()