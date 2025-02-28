import mysql.connector
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

    # Điều hướng tab "Quản Lý Máy Photocopy"
    if event == "Danh Sách Máy":
        show_content('machines_list')
        refresh_photocopy_table(window, inventory_manager, photocopy_page)
        due_machines = inventory_manager.check_maintenance_due()
        if due_machines:
            sg.popup("Các máy cần bảo trì:\n" + "\n".join([f"ID: {m[0]} - {m[1]}" for m in due_machines]), title="Cảnh Báo Bảo Trì")
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

    # Xử lý chọn vật tư
    elif event == "table":
        selected_rows = values["table"]
        if selected_rows:
            row = inventory_manager.fetch_all_items(offset=(vat_tu_page - 1) * 10, limit=10)
            current_item_id = row[selected_rows[0]][0]
            window["loai"].update(row[selected_rows[0]][1])
            window["nha_cung_cap"].update(row[selected_rows[0]][2])

    # Xóa vật tư hoặc máy photocopy
    elif event == "Xóa":
        if window.Element('TabGroup').Get() == 'Quản Lý Vật Tư':
            print("Đang xử lý xóa vật tư")
            selected_rows = values["table"]
            if selected_rows:
                item_id = inventory_manager.fetch_all_items(offset=(vat_tu_page - 1) * 10, limit=10)[selected_rows[0]][0]
                print(f"Đã chọn vật tư ID: {item_id}")
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
            print("Đang xử lý xóa máy photocopy")
            selected_rows = values["photocopy_table"]
            machines = inventory_manager.fetch_all_photocopy_machines(offset=(photocopy_page - 1) * 15, limit=15,
                                                                      force_refresh=True)
            if not machines:
                sg.popup("Danh sách máy hiện đang trống!")
                return current_item_id, selected_machine_id, vat_tu_page, photocopy_page
            if selected_rows and 0 <= selected_rows[0] < len(machines):
                machine_id = machines[selected_rows[0]][0]
                print(f"Đã chọn máy photocopy ID: {machine_id}")
                if sg.popup_yes_no(f"Bạn có chắc muốn xóa máy photocopy ID {machine_id}?") == "Yes":
                    if inventory_manager.delete_photocopy_machine(machine_id):
                        sg.popup("Xóa máy photocopy thành công!")
                        inventory_manager.machines_cache = None
                        refresh_photocopy_table(window, inventory_manager, photocopy_page)
                    else:
                        sg.popup_error("Không thể xóa máy!")
            else:
                sg.popup_error("Vui lòng chọn một máy hợp lệ để xóa!")

    # Cập nhật counter
    elif event == "update_counter":
        selected_rows = values["photocopy_table"]
        if selected_rows:
            machines = inventory_manager.fetch_all_photocopy_machines(offset=(photocopy_page - 1) * 15, limit=15)
            if selected_rows[0] < len(machines):
                machine_id = machines[selected_rows[0]][0]
                counter_window = sg.Window("Cập Nhật Counter", [
                    [sg.Text(f"Máy ID: {machine_id}"), sg.Text(f"Tên Máy: {machines[selected_rows[0]][2]}")],
                    [sg.Text("Số Counter Hiện Tại:"), sg.Text(str(machines[selected_rows[0]][3]))],
                    [sg.Text("Số Counter Mới:"), sg.Input(key="new_counter")],
                    [sg.Button("Xác Nhận"), sg.Button("Hủy"), sg.Button("Xem Lịch Sử Counter", key="view_counter_history")]
                ], size=(400, 200))
                while True:
                    counter_event, counter_values = counter_window.read()
                    if counter_event in (sg.WIN_CLOSED, "Hủy"):
                        break
                    elif counter_event == "Xác Nhận" and counter_values["new_counter"]:
                        try:
                            new_counter = int(counter_values["new_counter"])
                            if new_counter < machines[selected_rows[0]][3]:
                                sg.popup_error("Số counter mới phải lớn hơn hoặc bằng số hiện tại!")
                                continue
                            inventory_manager.cursor.execute(
                                "UPDATE photocopy_machines SET so_counter = %s WHERE id = %s",
                                (new_counter, machine_id)
                            )
                            inventory_manager.cursor.execute(
                                "INSERT INTO counter_history (machine_id, counter_value, record_date) VALUES (%s, %s, %s)",
                                (machine_id, new_counter, date.today())
                            )
                            inventory_manager.conn.commit()
                            inventory_manager.machines_cache = None
                            inventory_manager.counter_cache = None
                            refresh_photocopy_table(window, inventory_manager, photocopy_page)
                            sg.popup("Cập nhật counter thành công!")
                            break
                        except ValueError:
                            sg.popup_error("Số counter phải là số nguyên!")
                        except mysql.connector.Error as err:
                            sg.popup_error(f"Lỗi khi cập nhật counter: {err}")
                    elif counter_event == "view_counter_history":
                        history = inventory_manager.fetch_counter_history(machine_id, force_refresh=True)
                        if history:
                            sg.popup_scrolled("Lịch Sử Counter:\n" + "\n".join([f"{h[0]}: {h[1]}" for h in history]),
                                              title=f"Lịch Sử Counter Máy ID {machine_id}", size=(400, 300))
                        else:
                            sg.popup("Chưa có lịch sử counter cho máy này!")
                counter_window.close()

    # Kiểm tra bảo trì
    elif event == "check_maintenance":
        due_machines = inventory_manager.check_maintenance_due()
        if due_machines:
            sg.popup_scrolled("Các máy cần bảo trì:\n" + "\n".join([f"ID: {m[0]} - {m[1]}" for m in due_machines]),
                              title="Cảnh Báo Bảo Trì", size=(400, 300))
        else:
            sg.popup("Hiện không có máy nào cần bảo trì!")

    # Nhập hàng vật tư
    elif event == "Nhập Hàng":
        loai = values["loai"]
        nha_cung_cap = values["nha_cung_cap"]
        so_luong_nhap = values["so_luong_nhap"]
        gia_nhap_hang = values["gia_nhap_hang"]
        if not all([loai, nha_cung_cap, so_luong_nhap]):
            sg.popup_error("Vui lòng điền đầy đủ thông tin loại, nhà cung cấp và số lượng!")
        else:
            try:
                so_luong_nhap = int(so_luong_nhap)
                gia_nhap_hang = float(gia_nhap_hang) if gia_nhap_hang else None
                item_id = inventory_manager.import_item(loai, nha_cung_cap, so_luong_nhap, gia_nhap_hang)
                if item_id:
                    sg.popup(f"Nhập hàng thành công! ID vật tư: {item_id}")
                    window["so_luong_nhap"].update("")
                    window["gia_nhap_hang"].update("")
                    refresh_items_table(window, inventory_manager, vat_tu_page)
                    refresh_import_table(window, inventory_manager)
                else:
                    sg.popup_error("Nhập hàng thất bại!")
            except ValueError:
                sg.popup_error("Số lượng và giá nhập phải là số!")

    # Bán vật tư
    elif event == "Bán":
        so_luong_ban = values["so_luong_ban"]
        gia_ban = values["gia_ban"]
        customer_name = values["customer_name"]
        customer_phone = values["customer_phone"]
        if not current_item_id:
            sg.popup_error("Vui lòng chọn một vật tư để bán!")
        elif not all([so_luong_ban, gia_ban, customer_name, customer_phone]):
            sg.popup_error("Vui lòng điền đầy đủ thông tin bán hàng!")
        else:
            try:
                so_luong_ban = int(so_luong_ban)
                gia_ban = float(gia_ban)
                if inventory_manager.sell_item(current_item_id, so_luong_ban, gia_ban, customer_name, customer_phone):
                    sg.popup("Bán hàng thành công!")
                    window["so_luong_ban"].update("")
                    window["gia_ban"].update("")
                    window["customer_name"].update("")
                    window["customer_phone"].update("")
                    refresh_items_table(window, inventory_manager, vat_tu_page)
                    refresh_sales_table(window, inventory_manager)
                else:
                    sg.popup_error("Bán hàng thất bại!")
            except ValueError:
                sg.popup_error("Số lượng bán và giá bán phải là số!")

    # Nhập máy photocopy
    elif event == "Xác Nhận Nhập Máy":
        loai_may = values["import_loai_may"]
        ten_may = values["import_ten_may"]
        so_counter = values["import_so_counter"]
        gia_nhap_may = values["import_gia_nhap_may"]
        serial_number = values["import_serial_number"]
        if not all([loai_may, ten_may, so_counter, gia_nhap_may, serial_number]):
            sg.popup_error("Vui lòng điền đầy đủ thông tin nhập máy!")
        else:
            try:
                so_counter = int(so_counter)
                gia_nhap_may = float(gia_nhap_may)
                machine_id = inventory_manager.import_photocopy_machine(loai_may, ten_may, so_counter, gia_nhap_may, serial_number)
                if machine_id:
                    sg.popup(f"Nhập máy thành công! ID máy: {machine_id}")
                    window["import_loai_may"].update("")
                    window["import_ten_may"].update("")
                    window["import_so_counter"].update("")
                    window["import_gia_nhap_may"].update("")
                    window["import_serial_number"].update("")
                    refresh_photocopy_table(window, inventory_manager, photocopy_page)
            except ValueError:
                sg.popup_error("Số counter và giá nhập phải là số!")

    # Bán máy photocopy
    elif event == "photocopy_table":
        selected_rows = values["photocopy_table"]
        if selected_rows:
            machines = inventory_manager.fetch_all_photocopy_machines(offset=(photocopy_page - 1) * 15, limit=15)
            if selected_rows[0] < len(machines):
                selected_machine_id = machines[selected_rows[0]][0]
                window["sell_loai_may"].update(machines[selected_rows[0]][1])
                window["sell_ten_may"].update(machines[selected_rows[0]][2])
                window["sell_so_counter"].update(str(machines[selected_rows[0]][3]))
                window["sell_gia_nhap"].update(str(machines[selected_rows[0]][6]))
                window["sell_serial_number"].update(machines[selected_rows[0]][7])
    elif event == "Xác Nhận Bán Máy":
        if not selected_machine_id:
            sg.popup_error("Vui lòng chọn một máy để bán!")
        else:
            so_luong_ban_may = values["sell_so_luong_ban_may"]
            gia_ban_may = values["sell_gia_ban_may"]
            customer_name_may = values["sell_customer_name_may"]
            customer_phone_may = values["sell_customer_phone_may"]
            if not all([so_luong_ban_may, gia_ban_may, customer_name_may, customer_phone_may]):
                sg.popup_error("Vui lòng điền đầy đủ thông tin bán máy!")
            else:
                try:
                    so_luong_ban_may = int(so_luong_ban_may)
                    gia_ban_may = float(gia_ban_may)
                    if inventory_manager.sell_photocopy_machine(selected_machine_id, so_luong_ban_may, gia_ban_may,
                                                                customer_name_may, customer_phone_may):
                        sg.popup("Bán máy thành công!")
                        window["sell_so_luong_ban_may"].update("1")
                        window["sell_gia_ban_may"].update("")
                        window["sell_customer_name_may"].update("")
                        window["sell_customer_phone_may"].update("")
                        refresh_photocopy_table(window, inventory_manager, photocopy_page)
                        refresh_photocopy_sales_table(window, inventory_manager)
                    else:
                        sg.popup_error("Bán máy thất bại!")
                except ValueError:
                    sg.popup_error("Số lượng bán và giá bán phải là số!")

    # Cho thuê máy
    elif event == "Xác Nhận Cho Thuê":
        if not selected_machine_id:
            sg.popup_error("Vui lòng chọn một máy để cho thuê!")
        else:
            customer_name = values["rent_customer_name"]
            customer_phone = values["rent_customer_phone"]
            start_date = values["rent_start_date"]
            end_date = values["rent_end_date"]
            rental_price = values["rent_price"]
            if not all([customer_name, customer_phone, start_date, end_date, rental_price]):
                sg.popup_error("Vui lòng điền đầy đủ thông tin cho thuê!")
            else:
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    rental_price = float(rental_price)
                    if inventory_manager.rent_photocopy_machine(selected_machine_id, customer_name, customer_phone,
                                                                start_date, end_date, rental_price):
                        sg.popup("Cho thuê máy thành công!")
                        window["rent_customer_name"].update("")
                        window["rent_customer_phone"].update("")
                        window["rent_start_date"].update("")
                        window["rent_end_date"].update("")
                        window["rent_price"].update("")
                        refresh_photocopy_table(window, inventory_manager, photocopy_page)
                        refresh_rental_table(window, inventory_manager)
                    else:
                        sg.popup_error("Cho thuê máy thất bại!")
                except ValueError:
                    sg.popup_error("Ngày và giá thuê phải đúng định dạng!")

    # Trả máy
    elif event == "rental_table_return":
        selected_rows = values["rental_table_return"]
        if selected_rows:
            rentals = inventory_manager.fetch_rental_history()
            if selected_rows[0] < len(rentals):
                selected_rental = rentals[selected_rows[0]]
                window["return_machine_name"].update(selected_rental[0])
                window["return_customer_name_display"].update(selected_rental[1])
                window["return_customer_phone_display"].update(selected_rental[2])
                window["return_start_date"].update(str(selected_rental[3]))
                window["return_end_date"].update(str(selected_rental[4]))
                window["return_rental_price"].update(str(selected_rental[5]))
    elif event == "Xác Nhận Trả Máy":
        selected_rows = values["rental_table_return"]
        if not selected_rows:
            sg.popup_error("Vui lòng chọn một máy để trả!")
        else:
            return_date = values["return_date"]
            return_counter = values["return_counter"]
            return_customer_name = values["return_customer_name_input"]
            return_customer_phone = values["return_customer_phone_input"]
            if not all([return_date, return_counter, return_customer_name, return_customer_phone]):
                sg.popup_error("Vui lòng điền đầy đủ thông tin trả máy!")
            else:
                try:
                    rentals = inventory_manager.fetch_rental_history()
                    machine_id = inventory_manager.fetch_all_photocopy_machines()[selected_rows[0]][0]
                    return_date = datetime.strptime(return_date, '%Y-%m-%d').date()
                    return_counter = int(return_counter)
                    if inventory_manager.return_photocopy_machine(machine_id, return_date, return_counter,
                                                                  return_customer_name, return_customer_phone):
                        sg.popup("Trả máy thành công!")
                        window["return_date"].update("")
                        window["return_counter"].update("")
                        window["return_customer_name_input"].update("")
                        window["return_customer_phone_input"].update("")
                        refresh_photocopy_table(window, inventory_manager, photocopy_page)
                        refresh_rental_table(window, inventory_manager)
                    else:
                        sg.popup_error("Trả máy thất bại!")
                except ValueError:
                    sg.popup_error("Ngày trả và số counter phải đúng định dạng!")

    # Bảo trì máy
    elif event == "Xác Nhận Bảo Trì":
        if not selected_machine_id:
            sg.popup_error("Vui lòng chọn một máy để bảo trì!")
        else:
            desc = values["maintenance_desc"]
            cost = values["maintenance_cost"]
            if not all([desc, cost]):
                sg.popup_error("Vui lòng điền đầy đủ thông tin bảo trì!")
            else:
                try:
                    cost = float(cost)
                    if inventory_manager.add_maintenance_record(selected_machine_id, desc, cost):
                        sg.popup("Thêm bảo trì thành công!")
                        window["maintenance_desc"].update("")
                        window["maintenance_cost"].update("")
                        refresh_maintenance_table(window, inventory_manager)
                    else:
                        sg.popup_error("Thêm bảo trì thất bại!")
                except ValueError:
                    sg.popup_error("Chi phí phải là số!")

    # Phân trang vật tư
    elif event == "next_vat_tu":
        vat_tu_page += 1
        items = inventory_manager.fetch_all_items(offset=(vat_tu_page - 1) * 10, limit=10)
        if not items and vat_tu_page > 1:
            vat_tu_page -= 1
        refresh_items_table(window, inventory_manager, vat_tu_page)
    elif event == "prev_vat_tu":
        if vat_tu_page > 1:
            vat_tu_page -= 1
            refresh_items_table(window, inventory_manager, vat_tu_page)

    # Phân trang máy photocopy
    elif event == "next_photocopy":
        photocopy_page += 1
        machines = inventory_manager.fetch_all_photocopy_machines(offset=(photocopy_page - 1) * 15, limit=15)
        if not machines and photocopy_page > 1:
            photocopy_page -= 1
        refresh_photocopy_table(window, inventory_manager, photocopy_page)
    elif event == "prev_photocopy":
        if photocopy_page > 1:
            photocopy_page -= 1
            refresh_photocopy_table(window, inventory_manager, photocopy_page)

    # Thống kê
    elif event == "Thống Kê":
        if window.Element('TabGroup').Get() == 'Quản Lý Vật Tư':
            show_vat_tu_stats_window(inventory_manager)
        else:
            show_photocopy_detailed_stats_window(inventory_manager)

    # Xuất Excel
    elif event == "Xuất Excel":
        file_path = sg.popup_get_file("Chọn nơi lưu file Excel", save_as=True, file_types=(("Excel Files", "*.xlsx"),))
        if file_path:
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'
            current_tab = window.Element('TabGroup').Get()
            success = inventory_manager.export_to_excel(file_path, is_history=False,
                                                        is_photocopy=(current_tab == 'Quản Lý Máy Photocopy'))
            if not success:
                sg.popup_error("Không thể xuất file Excel!")

    # Xuất lịch sử
    elif event == "Xuất Lịch Sử":
        file_path = sg.popup_get_file("Chọn nơi lưu file Excel", save_as=True, file_types=(("Excel Files", "*.xlsx"),))
        if file_path:
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'
            current_tab = window.Element('TabGroup').Get()
            success = inventory_manager.export_to_excel(file_path, is_history=True,
                                                        is_photocopy=(current_tab == 'Quản Lý Máy Photocopy'))
            if not success:
                sg.popup_error("Không thể xuất file Excel!")

    # Xóa toàn bộ dữ liệu
    elif event == "Xóa Toàn Bộ Dữ Liệu" and user_role == 'admin':
        file_path = sg.popup_get_file("Chọn nơi lưu file backup", save_as=True, file_types=(("Excel Files", "*.xlsx"),))
        if file_path:
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'
            if inventory_manager.backup_all_data(file_path):
                if sg.popup_yes_no("Bạn có chắc chắn muốn xóa toàn bộ dữ liệu không?") == "Yes":
                    if inventory_manager.clear_all_data():
                        sg.popup("Xóa toàn bộ dữ liệu thành công!")
                        vat_tu_page = 1
                        photocopy_page = 1
                        refresh_items_table(window, inventory_manager, vat_tu_page)
                        refresh_sales_table(window, inventory_manager)
                        refresh_import_table(window, inventory_manager)
                        refresh_photocopy_table(window, inventory_manager, photocopy_page)
                        refresh_rental_table(window, inventory_manager)
                        refresh_maintenance_table(window, inventory_manager)
                        refresh_photocopy_sales_table(window, inventory_manager)

    # Làm mới
    elif event == "Làm Mới":
        current_tab = window.Element('TabGroup').Get()
        if current_tab == 'Quản Lý Vật Tư':
            refresh_items_table(window, inventory_manager, vat_tu_page)
            refresh_sales_table(window, inventory_manager)
            refresh_import_table(window, inventory_manager)
        else:
            refresh_photocopy_table(window, inventory_manager, photocopy_page)
            refresh_rental_table(window, inventory_manager)
            refresh_maintenance_table(window, inventory_manager)
            refresh_photocopy_sales_table(window, inventory_manager)

    return current_item_id, selected_machine_id, vat_tu_page, photocopy_page