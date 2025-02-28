import PySimpleGUI as sg

def refresh_items_table(window, inventory_manager, page=1):
    if window.Element('TabGroup').Get() == 'Quản Lý Vật Tư':
        offset = (page - 1) * 10
        items = inventory_manager.fetch_all_items(offset=offset, limit=10)
        window['table'].update(values=items)
        window['page_vat_tu'].update(f"Trang {page}")

def refresh_sales_table(window, inventory_manager):
    if window.Element('TabGroup').Get() == 'Quản Lý Vật Tư':
        sales_data = inventory_manager.fetch_sales_history()
        window['sales_table'].update(values=sales_data)

def refresh_import_table(window, inventory_manager):
    if window.Element('TabGroup').Get() == 'Quản Lý Vật Tư':
        import_data = inventory_manager.fetch_import_history()
        window['import_table'].update(values=import_data)

def refresh_photocopy_table(window, inventory_manager, page=1):
    if window.Element('TabGroup').Get() == 'Quản Lý Máy Photocopy':
        offset = (page - 1) * 15
        machines = inventory_manager.fetch_all_photocopy_machines(offset=offset, limit=15, force_refresh=True)
        window['photocopy_table'].update(values=machines)
        window['page_photocopy'].update(f"Trang {page}")

def refresh_rental_table(window, inventory_manager):
    if window.Element('TabGroup').Get() == 'Quản Lý Máy Photocopy':
        rental_data = inventory_manager.fetch_rental_history()
        window['rental_table'].update(values=rental_data)
        window['rental_table_return'].update(values=rental_data)

def refresh_maintenance_table(window, inventory_manager):
    if window.Element('TabGroup').Get() == 'Quản Lý Máy Photocopy':
        maintenance_data = inventory_manager.fetch_maintenance_history()
        window['maintenance_table'].update(values=maintenance_data)

def refresh_photocopy_sales_table(window, inventory_manager):
    if window.Element('TabGroup').Get() == 'Quản Lý Máy Photocopy':
        sales_data = inventory_manager.fetch_photocopy_sales_history()
        window['photocopy_sales_table'].update(values=sales_data)