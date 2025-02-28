import PySimpleGUI as sg
from datetime import datetime
from gui_refresh import (refresh_items_table, refresh_sales_table, refresh_import_table,
                         refresh_photocopy_table, refresh_rental_table, refresh_maintenance_table,
                         refresh_photocopy_sales_table)
from stats import show_vat_tu_stats_window, show_photocopy_detailed_stats_window


def handle_events(window, event, values, inventory_manager, current_item_id, selected_machine_id=None, vat_tu_page=1,
                  photocopy_page=1, user_role='user'):
    print(f"Sự kiện: {event}, Giá trị: {values}, Vai trò: {user_role}")

    content_keys = ['machines_list', 'import_machine', 'sell_machine', 'rent_machine', 'return_machine', 'maintenance']

    def show_content(content_key):
        for key in content_keys:
            window[key].update(visible=(key == content_key))

    if event == "Danh Sách Máy":
        show_content('machines_list')
        refresh_photocopy_table(window, inventory_manager, photocopy_page)
    elif event == "Nhập Máy":
        show_content('import_machine')
    elif event == "Bán Máy":
        show_content('sell_machine')
        refresh_photocopy_sales_table(window, inventory_manager)
    elif event == "Cho Thuê Máy":
        show_content('rent_machine')
        refresh_rental_table(window, inventory_manager)
    elif event == "Trả Máy":
        show_content('return_machine')
        refresh_rental_table(window, inventory_manager)
    elif event == "Bảo Trì":
        show_content('maintenance')
        refresh_maintenance_table(window, inventory_manager)
    elif event == "table":
        selected_rows = values["table"]
        if selected_rows:
            row = inventory_manager.fetch_all_items(offset=(vat_tu_page - 1) * 10, limit=10)
            current_item_id = row[selected_rows[0]][0]
            window["loai"].update(row[selected_rows[0]][1])
            window["nha_cung_cap"].update(row[selected_rows[0]][2])
    elif event == "Xóa":
        if window.Element('TabGroup').Get() == 'Quản Lý Vật Tư':
            selected_rows = values["table"]
            if selected_rows:
                item_id = inventory_manager.fetch_all_items(offset=(vat_tu_page - 1) * 10, limit=10)[selected_rows[0]][
                    0]
                if sg.popup_yes_no(f"Bạn có chắc muốn xóa vật tư ID {item_id}?") == "Yes":
                    if inventory_manager.delete_item(item_id):
                        sg.popup("Xóa thành công!")
                        current_item_id = None
                        refresh_items_table(window, inventory_manager, vat_tu_page)
                    else:
                        sg.popup_error("Không thể xóa vật tư!")
            else:
                sg.popup_error("Vui lòng chọn một vật tư để xóa!")
        else:
            selected_rows = values["photocopy_table"]
            machines = inventory_manager.fetch_all_photocopy_machines(offset=(photocopy_page - 1) * 15, limit=15,
                                                                      force_refresh=True)
            if not machines:
                sg.popup("Danh sách máy hiện đang trống!")
                return current_item_id, selected_machine_id, vat_tu_page, photocopy_page
            if selected_rows and 0 <= selected_rows[0] < len(machines):
                machine_id = machines[selected_rows[0]][0]
                if sg.popup_yes_no(f"Bạn có chắc muốn xóa máy photocopy ID {machine_id}?") == "Yes":
                    if inventory_manager.delete_photocopy_machine(machine_id):
                        sg.popup("Xóa máy photocopy thành công!")
                        inventory_manager.machines_cache = None
                        refresh_photocopy_table(window, inventory_manager, photocopy_page)
                    else:
                        sg.popup_error("Không thể xóa máy!")
            else:
                sg.popup_error("Vui lòng chọn một máy hợp lệ để xóa!")
    elif event == "Bán":
        if current_item_id and values["so_luong_ban"] and values["gia_ban"] and values["customer_name"] and values[
            "customer_phone"]:
            try:
                quantity = int(values["so_luong_ban"])
                price = float(values["gia_ban"])
                customer_name = values["customer_name"].strip()
                customer_phone = values["customer_phone"].strip()
                if inventory_manager.sell_item(current_item_id, quantity, price, customer_name, customer_phone):
                    sg.popup("Bán hàng thành công!")
                    refresh_items_table(window, inventory_manager, vat_tu_page)
                    refresh_sales_table(window, inventory_manager)
                    window["so_luong_ban"].update("")
                    window["gia_ban"].update("")
                    window["customer_name"].update("")
                    window["customer_phone"].update("")
            except ValueError as e:
                sg.popup_error(f"Lỗi dữ liệu: {e}")
        else:
            sg.popup_error("Vui lòng chọn vật tư và nhập đủ thông tin bán hàng!")
    elif event == "Nhập Hàng":
        try:
            loai = values["loai"].strip()
            nha_cung_cap = values["nha_cung_cap"].strip()
            so_luong_nhap = values["so_luong_nhap"].strip()
            gia_nhap_hang = values["gia_nhap_hang"].strip()
            if not loai or not nha_cung_cap or not so_luong_nhap:
                sg.popup_error("Vui lòng nhập đầy đủ Loại, Nhà Cung Cấp và Số Lượng Nhập!")
                return current_item_id, selected_machine_id, vat_tu_page, photocopy_page
            quantity = int(so_luong_nhap)
            price = float(gia_nhap_hang) if gia_nhap_hang else None
            item_id = inventory_manager.import_item(loai, nha_cung_cap, quantity, price)
            if item_id:
                current_item_id = item_id
                sg.popup("Nhập hàng thành công!")
                refresh_items_table(window, inventory_manager, vat_tu_page)
                refresh_import_table(window, inventory_manager)
                window["so_luong_nhap"].update("")
                window["gia_nhap_hang"].update("")
            else:
                sg.popup_error("Không thể nhập hàng!")
        except ValueError as e:
            sg.popup_error(f"Lỗi dữ liệu nhập hàng: {e}")
    elif event == "photocopy_table":
        selected_rows = values["photocopy_table"]
        if selected_rows:
            # Lấy danh sách máy từ photocopy_machines
            machines = inventory_manager.fetch_all_photocopy_machines(offset=(photocopy_page - 1) * 15, limit=15,
                                                                      force_refresh=True)
            if not machines:
                sg.popup_error("Không có máy nào trong kho!")
                return current_item_id, selected_machine_id, vat_tu_page, photocopy_page

            machine = machines[selected_rows[0]]
            selected_machine_id = machine[0]

            # Cập nhật thông tin cơ bản từ photocopy_machines (nếu máy còn trong kho)
            window["sell_loai_may"].update(machine[1])
            window["sell_ten_may"].update(machine[2])
            window["sell_so_counter"].update(str(machine[3]))
            window["sell_gia_nhap"].update(f"{machine[6]:,.2f} VND")
            window["sell_serial_number"].update(machine[7])
            window["rent_loai_may"].update(machine[1])
            window["rent_ten_may"].update(machine[2])
            window["rent_so_counter"].update(str(machine[3]))
            window["rent_gia_nhap"].update(f"{machine[6]:,.2f} VND")
            window["rent_serial_number"].update(machine[7])

            # Kiểm tra lịch sử bán để lấy thông tin khách hàng (bao gồm máy đã bán)
            try:
                # Kiểm tra trong photocopy_sales_history cho máy đã bán
                inventory_manager.cursor.execute(
                    "SELECT customer_name, customer_phone FROM photocopy_sales_history WHERE machine_id = %s ORDER BY sale_date DESC LIMIT 1",
                    (selected_machine_id,)
                )
                sale_info = inventory_manager.cursor.fetchone()
                if sale_info:
                    window["sell_customer_name_may"].update(sale_info[0] or "")
                    window["sell_customer_phone_may"].update(sale_info[1] or "")
                else:
                    # Nếu không tìm thấy trong lịch sử bán, kiểm tra máy còn trong kho không
                    inventory_manager.cursor.execute(
                        "SELECT trang_thai FROM photocopy_machines WHERE id = %s",
                        (selected_machine_id,)
                    )
                    machine_status = inventory_manager.cursor.fetchone()
                    if machine_status and machine_status[0] == 'Trong Kho':
                        window["sell_customer_name_may"].update("")
                        window["sell_customer_phone_may"].update("")
                    else:
                        sg.popup_error(f"Máy ID {selected_machine_id} đã được bán, không còn trong kho!")
                        window["sell_customer_name_may"].update("")
                        window["sell_customer_phone_may"].update("")
            except mysql.connector.Error as err:
                sg.popup_error(f"Lỗi khi lấy thông tin bán: {err}")
                window["sell_customer_name_may"].update("")
                window["sell_customer_phone_may"].update("")

            print(f"Đã chọn máy photocopy ID {selected_machine_id}")
    elif event == "Xác Nhận Nhập Máy":
        try:
            loai_may = values["import_loai_may"].strip()
            ten_may = values["import_ten_may"].strip()
            so_counter = values["import_so_counter"].strip()
            gia_nhap_may = values["import_gia_nhap_may"].strip()
            serial_number = values["import_serial_number"].strip()
            if not loai_may or not ten_may or not so_counter or not gia_nhap_may or not serial_number:
                sg.popup_error("Vui lòng nhập đầy đủ thông tin máy, bao gồm số serial!")
                return current_item_id, selected_machine_id, vat_tu_page, photocopy_page
            so_counter = int(so_counter)
            gia_nhap = float(gia_nhap_may)
            machine_id = inventory_manager.import_photocopy_machine(loai_may, ten_may, so_counter, gia_nhap,
                                                                    serial_number)
            if machine_id:
                sg.popup("Nhập máy photocopy thành công!")
                inventory_manager.machines_cache = None
                refresh_photocopy_table(window, inventory_manager, photocopy_page)
                show_content('machines_list')
                window["import_loai_may"].update("")
                window["import_ten_may"].update("")
                window["import_so_counter"].update("")
                window["import_gia_nhap_may"].update("")
                window["import_serial_number"].update("")
                print(f"Đã làm mới bảng sau khi nhập máy ID {machine_id}")
            else:
                sg.popup_error("Không thể nhập máy!")
        except ValueError as e:
            sg.popup_error(f"Lỗi dữ liệu nhập máy: {e}")
    elif event == "Xác Nhận Bán Máy":
        if values["sell_so_luong_ban_may"] and values["sell_gia_ban_may"] and values["sell_customer_name_may"] and \
                values["sell_customer_phone_may"]:
            try:
                selected_rows = values["photocopy_table"]
                if not selected_rows:
                    sg.popup_error("Vui lòng chọn một máy photocopy từ danh sách để bán!")
                    return current_item_id, selected_machine_id, vat_tu_page, photocopy_page
                machines = inventory_manager.fetch_all_photocopy_machines(offset=(photocopy_page - 1) * 15, limit=15)
                if not machines:
                    sg.popup_error("Không có máy nào trong danh sách để bán!")
                    return current_item_id, selected_machine_id, vat_tu_page, photocopy_page
                machine = machines[selected_rows[0]]
                machine_id = machine[0]
                quantity = int(values["sell_so_luong_ban_may"])
                price = float(values["sell_gia_ban_may"])
                customer_name = values["sell_customer_name_may"].strip()
                customer_phone = values["sell_customer_phone_may"].strip()
                if inventory_manager.sell_photocopy_machine(machine_id, quantity, price, customer_name, customer_phone):
                    sg.popup("Bán máy photocopy thành công!")
                    inventory_manager.machines_cache = None
                    refresh_photocopy_table(window, inventory_manager, photocopy_page)
                    refresh_photocopy_sales_table(window, inventory_manager)
                    window["sell_so_luong_ban_may"].update("")
                    window["sell_gia_ban_may"].update("")
                    window["sell_customer_name_may"].update("")
                    window["sell_customer_phone_may"].update("")
                    window["sell_customer_email_may"].update("")
                    window["sell_loai_may"].update("")
                    window["sell_ten_may"].update("")
                    window["sell_so_counter"].update("")
                    window["sell_gia_nhap"].update("")
                    window["sell_serial_number"].update("")
                    show_content('sell_machine')
                else:
                    sg.popup_error("Không thể bán máy, kiểm tra trạng thái hoặc dữ liệu!")
            except ValueError as e:
                sg.popup_error(f"Lỗi dữ liệu: {e}")
        else:
            sg.popup_error("Vui lòng nhập đủ thông tin bán máy!")
    elif event == "Xác Nhận Cho Thuê":
        if values["rent_customer_name"] and values["rent_customer_phone"] and values["rent_start_date"] and values[
            "rent_end_date"] and values["rent_price"]:
            try:
                selected_rows = values["photocopy_table"]
                if not selected_rows:
                    sg.popup_error("Vui lòng chọn một máy photocopy từ danh sách để cho thuê!")
                    return current_item_id, selected_machine_id, vat_tu_page, photocopy_page
                machines = inventory_manager.fetch_available_photocopy_machines(offset=(photocopy_page - 1) * 15,
                                                                                limit=15)
                if not machines:
                    sg.popup_error("Không có máy nào trong kho để cho thuê!")
                    return current_item_id, selected_machine_id, vat_tu_page, photocopy_page
                machine = machines[selected_rows[0]]
                machine_id = machine[0]
                start_date = datetime.strptime(values["rent_start_date"], "%Y-%m-%d").date()
                end_date = datetime.strptime(values["rent_end_date"], "%Y-%m-%d").date()
                if start_date > end_date:
                    sg.popup_error("Ngày bắt đầu phải nhỏ hơn ngày kết thúc!")
                    return current_item_id, selected_machine_id, vat_tu_page, photocopy_page
                rental_price = float(values["rent_price"])
                customer_name = values["rent_customer_name"].strip()
                customer_phone = values["rent_customer_phone"].strip()
                if inventory_manager.rent_photocopy_machine(machine_id, customer_name, customer_phone, start_date,
                                                            end_date, rental_price):
                    sg.popup("Cho thuê máy photocopy thành công!")
                    inventory_manager.machines_cache = None
                    refresh_photocopy_table(window, inventory_manager, photocopy_page)
                    refresh_rental_table(window, inventory_manager)
                    window["rent_customer_name"].update("")
                    window["rent_customer_phone"].update("")
                    window["rent_start_date"].update("")
                    window["rent_end_date"].update("")
                    window["rent_price"].update("")
                    window["rent_loai_may"].update("")
                    window["rent_ten_may"].update("")
                    window["rent_so_counter"].update("")
                    window["rent_gia_nhap"].update("")
                    window["rent_serial_number"].update("")
                    show_content('rent_machine')
            except ValueError as e:
                sg.popup_error(f"Lỗi dữ liệu: {e}")
        else:
            sg.popup_error("Vui lòng nhập đủ thông tin cho thuê máy!")
    elif event == "rental_table_return":
        selected_rows = values["rental_table_return"]
        if selected_rows:
            rentals = inventory_manager.fetch_rental_history()
            if rentals and selected_rows[0] < len(rentals):
                rental = rentals[selected_rows[0]]
                window["return_machine_name"].update(rental[0])
                window["return_customer_name_display"].update(rental[1])
                window["return_customer_phone_display"].update(rental[2])
                window["return_start_date"].update(str(rental[3]))
                window["return_end_date"].update(str(rental[4]))
                window["return_rental_price"].update(f"{rental[5]:,.2f} VND")
    elif event == "Xác Nhận Trả Máy":
        if values["return_date"] and values["return_counter"] and values["return_customer_name_input"] and values[
            "return_customer_phone_input"]:
            selected_rows = values["rental_table_return"]
            if selected_rows:
                rentals = inventory_manager.fetch_rental_history()
                if not rentals or selected_rows[0] >= len(rentals):
                    sg.popup_error("Không có máy nào đang cho thuê hoặc bản ghi không hợp lệ!")
                    return current_item_id, selected_machine_id, vat_tu_page, photocopy_page
                machine_name = rentals[selected_rows[0]][0]
                inventory_manager.cursor.execute(
                    "SELECT id FROM photocopy_machines WHERE ten_may = %s AND trang_thai = 'Đang Cho Thuê'",
                    (machine_name,)
                )
                machine = inventory_manager.cursor.fetchone()
                if not machine:
                    sg.popup_error(f"Máy {machine_name} không đang cho thuê!")
                    return current_item_id, selected_machine_id, vat_tu_page, photocopy_page
                machine_id = machine[0]
                try:
                    return_date = datetime.strptime(values["return_date"], "%Y-%m-%d").date()
                    return_counter = int(values["return_counter"])
                    return_customer_name = values["return_customer_name_input"].strip()
                    return_customer_phone = values["return_customer_phone_input"].strip()
                    if inventory_manager.return_photocopy_machine(machine_id, return_date, return_counter,
                                                                  return_customer_name, return_customer_phone):
                        sg.popup("Trả máy photocopy thành công!")
                        inventory_manager.machines_cache = None
                        refresh_photocopy_table(window, inventory_manager, photocopy_page)
                        refresh_rental_table(window, inventory_manager)
                        window["return_date"].update("")
                        window["return_counter"].update("")
                        window["return_customer_name_input"].update("")
                        window["return_customer_phone_input"].update("")
                        window["return_machine_name"].update("")
                        window["return_customer_name_display"].update("")
                        window["return_customer_phone_display"].update("")
                        window["return_start_date"].update("")
                        window["return_end_date"].update("")
                        window["return_rental_price"].update("")
                        show_content('return_machine')
                except ValueError as e:
                    sg.popup_error(f"Lỗi dữ liệu: {e}")
            else:
                sg.popup_error("Vui lòng chọn một máy đang cho thuê để trả!")
        else:
            sg.popup_error(
                "Vui lòng nhập đầy đủ thông tin trả máy: Ngày Trả, Số Counter Trả, Tên và SĐT Khách Hàng Trả!")
    elif event == "Xác Nhận Bảo Trì":
        selected_rows = values["photocopy_table"]
        if not selected_rows:
            sg.popup_error("Vui lòng chọn một máy photocopy từ danh sách để thêm bảo trì!")
            return current_item_id, selected_machine_id, vat_tu_page, photocopy_page
        machine_id = \
        inventory_manager.fetch_all_photocopy_machines(offset=(photocopy_page - 1) * 15, limit=15)[selected_rows[0]][0]
        desc = values["maintenance_desc"].strip()
        try:
            cost = float(values["maintenance_cost"] or 0)
            if inventory_manager.add_maintenance_record(machine_id, desc, cost):
                sg.popup("Thêm bảo trì thành công!")
                refresh_photocopy_table(window, inventory_manager, photocopy_page)
                refresh_maintenance_table(window, inventory_manager)
                window["maintenance_desc"].update("")
                window["maintenance_cost"].update("")
                show_content('maintenance')
            else:
                sg.popup_error("Không thể thêm bảo trì!")
        except ValueError:
            sg.popup_error("Chi phí phải là số hợp lệ!")
    elif event == "Tìm":
        search_text = values["Search"]
        filtered_data = [row for row in inventory_manager.fetch_all_items(offset=0, limit=1000) if
                         search_text.lower() in str(row).lower()]
        display_filtered = [[row[0], row[1], row[2], row[3], row[4] if row[4] is not None else 0] for row in
                            filtered_data]
        window['table'].update(values=display_filtered[:10])
        window['page_vat_tu'].update("Trang 1 (Tìm kiếm)")
    elif event == "prev_vat_tu" and vat_tu_page > 1:
        vat_tu_page -= 1
        refresh_items_table(window, inventory_manager, vat_tu_page)
    elif event == "next_vat_tu":
        vat_tu_page += 1
        items = inventory_manager.fetch_all_items(offset=(vat_tu_page - 1) * 10, limit=10)
        if not items and vat_tu_page > 1:
            vat_tu_page -= 1
        refresh_items_table(window, inventory_manager, vat_tu_page)
    elif event == "prev_photocopy" and photocopy_page > 1:
        photocopy_page -= 1
        refresh_photocopy_table(window, inventory_manager, photocopy_page)
    elif event == "next_photocopy":
        photocopy_page += 1
        machines = inventory_manager.fetch_all_photocopy_machines(offset=(photocopy_page - 1) * 15, limit=15)
        if not machines and photocopy_page > 1:
            photocopy_page -= 1
        refresh_photocopy_table(window, inventory_manager, photocopy_page)
    elif event == "Xóa Toàn Bộ Dữ Liệu":
        if user_role != 'admin':
            sg.popup_error("Chỉ quản trị viên (admin) mới có quyền xóa toàn bộ dữ liệu!",
                           title="Quyền truy cập bị từ chối")
        else:
            if sg.popup_yes_no(
                    "Bạn có chắc chắn muốn xóa toàn bộ dữ liệu?\nHành động này sẽ xóa tất cả vật tư, máy photocopy, lịch sử bán/thuê (trừ thông tin người dùng).\nDữ liệu sẽ được backup trước khi xóa!",
                    title="Cảnh báo") == "Yes":
                backup_path = sg.popup_get_file("Chọn nơi lưu file backup", save_as=True,
                                                file_types=(("Excel Files", "*.xlsx"),), default_extension=".xlsx")
                if backup_path:
                    if not backup_path.endswith('.xlsx'):
                        backup_path += '.xlsx'
                    if inventory_manager.backup_all_data(backup_path):
                        if inventory_manager.clear_all_data():
                            sg.popup("Đã xóa toàn bộ dữ liệu thành công! Dữ liệu đã được backup tại: " + backup_path)
                            refresh_items_table(window, inventory_manager, vat_tu_page)
                            refresh_sales_table(window, inventory_manager)
                            refresh_import_table(window, inventory_manager)
                            refresh_photocopy_table(window, inventory_manager, photocopy_page)
                            refresh_rental_table(window, inventory_manager)
                            refresh_maintenance_table(window, inventory_manager)
                            refresh_photocopy_sales_table(window, inventory_manager)
                        else:
                            sg.popup_error("Không thể xóa dữ liệu!")
                    else:
                        sg.popup_error("Backup thất bại, không tiếp tục xóa dữ liệu!")
                else:
                    sg.popup_error("Vui lòng chọn đường dẫn backup để tiếp tục!")
    elif event == "Làm Mới":
        inventory_manager.items_cache = None
        inventory_manager.sales_cache = None
        inventory_manager.import_cache = None
        inventory_manager.machines_cache = None
        inventory_manager.photocopy_sales_cache = None
        inventory_manager.rental_cache = None
        inventory_manager.maintenance_cache = None
        refresh_items_table(window, inventory_manager, vat_tu_page)
        refresh_sales_table(window, inventory_manager)
        refresh_import_table(window, inventory_manager)
        refresh_photocopy_table(window, inventory_manager, photocopy_page)
        refresh_rental_table(window, inventory_manager)
        refresh_maintenance_table(window, inventory_manager)
        refresh_photocopy_sales_table(window, inventory_manager)
        sg.popup("Đã làm mới toàn bộ dữ liệu!")
    elif event in ("Xuất Excel", "Xuất Lịch Sử"):
        file_path = sg.popup_get_file("Lưu file Excel", save_as=True, file_types=(("Excel Files", "*.xlsx"),),
                                      default_extension=".xlsx")
        if file_path:
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'
            is_photocopy = window.Element('TabGroup').Get() == 'Quản Lý Máy Photocopy'
            is_history = "history" in file_path.lower() or event == "Xuất Lịch Sử"
            if inventory_manager.export_to_excel(file_path, is_history, is_photocopy):
                sg.popup("Xuất Excel thành công!")
    elif event == "Thống Kê":
        if window.Element('TabGroup').Get() == 'Quản Lý Vật Tư':
            show_vat_tu_stats_window(inventory_manager)
        else:
            show_photocopy_detailed_stats_window(inventory_manager)
    elif event == "Thoát":
        window.close()

    return current_item_id, selected_machine_id, vat_tu_page, photocopy_page


if __name__ == "__main__":
    print("This module is not meant to be run directly. Please run main.py instead.")