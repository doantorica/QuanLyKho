import PySimpleGUI as sg

def refresh_items_table(window, inventory_manager, page=1):
    if window.Element('TabGroup').Get() == 'Quản Lý Vật Tư':
        limit = 10
        offset = (page - 1) * limit
        items = inventory_manager.fetch_all_items(offset=offset, limit=limit)
        if items is None or not items:
            display_items = []
        else:
            display_items = [[row[0], row[1], row[2], row[3], row[4] if row[4] is not None else 0] for row in items]
        window['table'].update(values=display_items)
        window['page_vat_tu'].update(f"Trang {page}")

def refresh_sales_table(window, inventory_manager):
    if window.Element('TabGroup').Get() == 'Quản Lý Vật Tư':
        sales = inventory_manager.fetch_sales_history()
        if sales is None or not sales:
            window['sales_table'].update(values=[])
        else:
            window['sales_table'].update(values=sales)

def refresh_import_table(window, inventory_manager):
    if window.Element('TabGroup').Get() == 'Quản Lý Vật Tư':
        imports = inventory_manager.fetch_import_history()
        if imports is None or not imports:
            window['import_table'].update(values=[])
        else:
            window['import_table'].update(values=imports)

def refresh_photocopy_table(window, inventory_manager, page=1):
    if window.Element('TabGroup').Get() == 'Quản Lý Máy Photocopy':
        limit = 15
        offset = (page - 1) * limit
        # Luôn lấy dữ liệu mới từ cơ sở dữ liệu với force_refresh=True
        machines = inventory_manager.fetch_all_photocopy_machines(offset=offset, limit=limit, force_refresh=True)
        if machines is None or not machines:
            display_machines = []
        else:
            # Đảm bảo trạng thái không bao giờ là None khi hiển thị
            display_machines = [
                [row[0], row[1], row[2], row[3], row[4] if row[4] is not None else 'Trong Kho', row[5], row[6], row[7]]
                for row in machines
            ]
        window['photocopy_table'].update(values=display_machines)
        window['page_photocopy'].update(f"Trang {page}")
        print(f"Đã cập nhật bảng photocopy_table với {len(display_machines)} mục")

def refresh_rental_table(window, inventory_manager):
    if window.Element('TabGroup').Get() == 'Quản Lý Máy Photocopy':
        rentals = inventory_manager.fetch_rental_history()
        if rentals is None or not rentals:
            display_rentals = []
        else:
            display_rentals = [[ "" if val is None else val for val in row] for row in rentals]
        window['rental_table'].update(values=display_rentals)
        window['rental_table_return'].update(values=display_rentals)

def refresh_maintenance_table(window, inventory_manager):
    if window.Element('TabGroup').Get() == 'Quản Lý Máy Photocopy':
        maintenance_data = inventory_manager.fetch_maintenance_history()
        if maintenance_data is None or not maintenance_data:
            display_data = []
        else:
            display_data = [[row[0], row[1], row[2], f"{row[3]:,.2f}" if row[3] is not None else "0"] for row in maintenance_data]
        window['maintenance_table'].update(values=display_data)

def refresh_photocopy_sales_table(window, inventory_manager):
    if window.Element('TabGroup').Get() == 'Quản Lý Máy Photocopy':
        sales = inventory_manager.fetch_photocopy_sales_history()
        if sales is None or not sales:
            display_sales = []
        else:
            display_sales = [[ "" if val is None else val for val in row] for row in sales]
        window['photocopy_sales_table'].update(values=display_sales)