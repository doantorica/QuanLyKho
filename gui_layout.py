import PySimpleGUI as sg

PRODUCT_TYPES = ["Drum Color", "Drum Bk", "Mực Vàng", "Mực Đỏ", "Mực Xanh", "Mực Đen",
                 "Gạt Drum color", "Gạt Drum Bk", "Gạt Flim", "Flim Sấy", "Flim ảnh"]

def create_layout():
    sg.theme('LightGrey1')
    input_size = (35, 1)
    label_size = (15, 1)
    button_size = (15, 1)

    vat_tu_tab = [
        [sg.Text("Tìm kiếm:", font=('Helvetica', 10)), sg.Input(key='Search', size=(30, 1)),
         sg.Button("Tìm", size=(10, 1))],
        [sg.Frame("Thông Tin Vật Tư", [
            [sg.Column([
                [sg.Text("Loại", size=label_size, font=('Helvetica', 10)),
                 sg.Combo(PRODUCT_TYPES, key="loai", size=input_size, font=('Helvetica', 10))],
                [sg.Text("Nhà Cung Cấp", size=label_size, font=('Helvetica', 10)),
                 sg.Input(key="nha_cung_cap", size=input_size, font=('Helvetica', 10))]
            ], pad=(10, 10))]
        ], font=('Helvetica', 11, 'bold'), pad=(10, 10), expand_x=True)],
        [sg.Frame("Thông Tin Nhập Hàng", [
            [sg.Column([
                [sg.Text("Số Lượng Nhập", size=label_size, font=('Helvetica', 10)),
                 sg.Input(key="so_luong_nhap", size=input_size, font=('Helvetica', 10))],
                [sg.Text("Giá Nhập Hàng", size=label_size, font=('Helvetica', 10)),
                 sg.Input(key="gia_nhap_hang", size=input_size, font=('Helvetica', 10))],
            ], pad=(10, 10), background_color='#d4edda')],
            [sg.Column([[
                sg.Button("Nhập Hàng", size=button_size, font=('Helvetica', 10), button_color=('white', '#17a2b8'))
            ]], justification='center', pad=(0, 5), expand_x=True)]
        ], font=('Helvetica', 11, 'bold'), background_color='#28a745', title_color='white', pad=(10, 10),
                  expand_x=True)],
        [sg.Frame("Thông Tin Bán Hàng", [
            [sg.Column([
                [sg.Text("Số Lượng Bán", size=label_size, font=('Helvetica', 10)),
                 sg.Input(key="so_luong_ban", size=input_size, font=('Helvetica', 10))],
                [sg.Text("Giá Bán", size=label_size, font=('Helvetica', 10)),
                 sg.Input(key="gia_ban", size=input_size, font=('Helvetica', 10))],
                [sg.Text("Tên Khách Hàng", size=label_size, font=('Helvetica', 10)),
                 sg.Input(key="customer_name", size=input_size, font=('Helvetica', 10))],
                [sg.Text("SĐT Khách Hàng", size=label_size, font=('Helvetica', 10)),
                 sg.Input(key="customer_phone", size=input_size, font=('Helvetica', 10))],
            ], pad=(10, 10), background_color='#e9ecef')],
            [sg.Column([[
                sg.Button("Xóa", size=button_size, font=('Helvetica', 10), button_color=('white', '#dc3545')),
                sg.Button("Bán", size=button_size, font=('Helvetica', 10), button_color=('white', '#17a2b8'))
            ]], justification='center', pad=(0, 5), expand_x=True)]
        ], font=('Helvetica', 11, 'bold'), background_color='#6c757d', title_color='white', pad=(10, 10),
                  expand_x=True)],
        [sg.Column([
            [sg.Frame("Danh Sách Vật Tư", [
                [sg.Table(values=[], headings=["ID", "Loại", "Nhà Cung Cấp", "Số Lượng Tồn", "Giá Nhập"], key='table',
                          enable_events=True, auto_size_columns=False, col_widths=[8, 25, 25, 15, 15],
                          justification='center', num_rows=10, row_height=30, font=('Helvetica', 10),
                          header_font=('Helvetica', 10, 'bold'), expand_x=True)],
                [sg.Button("Trang Trước", key="prev_vat_tu"), sg.Button("Trang Sau", key="next_vat_tu"),
                 sg.Text("Trang 1", key="page_vat_tu")]
            ], font=('Helvetica', 11, 'bold'), pad=(5, 5), expand_x=True)],
            [sg.Frame("Lịch Sử Bán Hàng", [
                [sg.Table(values=[],
                          headings=["Loại", "Số Lượng", "Ngày Bán", "Giá Bán", "Doanh Thu", "Tên Khách Hàng", "SĐT"],
                          key='sales_table',
                          auto_size_columns=False, col_widths=[20, 10, 15, 15, 15, 20, 15], justification='center',
                          num_rows=10, row_height=30, font=('Helvetica', 10), header_font=('Helvetica', 10, 'bold'),
                          expand_x=True)]
            ], font=('Helvetica', 11, 'bold'), pad=(5, 5), expand_x=True)],
            [sg.Frame("Lịch Sử Nhập Hàng", [
                [sg.Table(values=[], headings=["Loại", "Số Lượng", "Ngày Nhập", "Giá Nhập"], key='import_table',
                          auto_size_columns=False, col_widths=[25, 12, 18, 15], justification='center',
                          num_rows=10, row_height=30, font=('Helvetica', 10), header_font=('Helvetica', 10, 'bold'),
                          expand_x=True)]
            ], font=('Helvetica', 11, 'bold'), pad=(5, 5), expand_x=True)]
        ], scrollable=True, vertical_scroll_only=True, size=(900, 300), expand_x=True, expand_y=True)]
    ]

    photocopy_nav = [
        [sg.Button("Danh Sách Máy", size=(15, 1), font=('Helvetica', 10)),
         sg.Button("Nhập Máy", size=(15, 1), font=('Helvetica', 10)),
         sg.Button("Bán Máy", size=(15, 1), font=('Helvetica', 10)),
         sg.Button("Cho Thuê Máy", size=(15, 1), font=('Helvetica', 10)),
         sg.Button("Trả Máy", size=(15, 1), font=('Helvetica', 10)),
         sg.Button("Bảo Trì", size=(15, 1), font=('Helvetica', 10))]
    ]

    machines_list_content = [
        [sg.Table(values=[],
                  headings=["ID", "Loại Máy", "Tên Máy", "Số Counter", "Trạng Thái", "Ngày Nhập", "Giá Nhập", "Số Serial"],
                  key='photocopy_table',
                  enable_events=True, auto_size_columns=False, col_widths=[8, 15, 20, 15, 15, 15, 15, 20],
                  justification='center', num_rows=15, row_height=30, font=('Helvetica', 10),
                  header_font=('Helvetica', 10, 'bold'), expand_x=True, expand_y=True)],
        [sg.Button("Trang Trước", key="prev_photocopy"), sg.Button("Trang Sau", key="next_photocopy"),
         sg.Text("Trang 1", key="page_photocopy"), sg.Button("Xóa Máy", button_color=('white', '#dc3545'))]
    ]

    import_machine_content = [
        [sg.Text("Loại Máy", size=label_size, font=('Helvetica', 10)),
         sg.Combo(['Đen Trắng', 'Màu'], key="import_loai_may", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Tên Máy", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="import_ten_may", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Số Counter", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="import_so_counter", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Giá Nhập Máy", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="import_gia_nhap_may", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Số Serial", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="import_serial_number", size=input_size, font=('Helvetica', 10))],
        [sg.Button("Xác Nhận Nhập Máy", size=button_size, font=('Helvetica', 10), button_color=('white', '#28a745'))]
    ]

    sell_machine_content = [
        [sg.Text("Loại Máy", size=label_size, font=('Helvetica', 10)),
         sg.Text("", key="sell_loai_may", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Tên Máy", size=label_size, font=('Helvetica', 10)),
         sg.Text("", key="sell_ten_may", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Số Counter", size=label_size, font=('Helvetica', 10)),
         sg.Text("", key="sell_so_counter", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Giá Nhập", size=label_size, font=('Helvetica', 10)),
         sg.Text("", key="sell_gia_nhap", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Số Serial", size=label_size, font=('Helvetica', 10)),
         sg.Text("", key="sell_serial_number", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Số Lượng Bán", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="sell_so_luong_ban_may", size=input_size, default_text="1", font=('Helvetica', 10))],
        [sg.Text("Giá Bán", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="sell_gia_ban_may", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Tên Khách Hàng", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="sell_customer_name_may", size=input_size, font=('Helvetica', 10))],  # Loại bỏ readonly
        [sg.Text("SĐT Khách Hàng", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="sell_customer_phone_may", size=input_size, font=('Helvetica', 10))],  # Loại bỏ readonly
        [sg.Text("Email Khách Hàng", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="sell_customer_email_may", size=input_size, font=('Helvetica', 10))],
        [sg.Button("Xác Nhận Bán Máy", size=button_size, font=('Helvetica', 10), button_color=('white', '#17a2b8'))],
        [sg.Table(values=[],
                  headings=["Tên Máy", "Ngày Bán", "Giá Bán", "Tên Khách Hàng", "SĐT"],
                  key='photocopy_sales_table',
                  auto_size_columns=False, col_widths=[20, 15, 15, 20, 15],
                  justification='center', num_rows=10, row_height=30, font=('Helvetica', 10),
                  header_font=('Helvetica', 10, 'bold'), expand_x=True)]
    ]

    rent_machine_content = [
        [sg.Text("Loại Máy", size=label_size, font=('Helvetica', 10)),
         sg.Text("", key="rent_loai_may", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Tên Máy", size=label_size, font=('Helvetica', 10)),
         sg.Text("", key="rent_ten_may", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Số Counter", size=label_size, font=('Helvetica', 10)),
         sg.Text("", key="rent_so_counter", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Giá Nhập", size=label_size, font=('Helvetica', 10)),
         sg.Text("", key="rent_gia_nhap", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Số Serial", size=label_size, font=('Helvetica', 10)),
         sg.Text("", key="rent_serial_number", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Tên Khách Hàng", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="rent_customer_name", size=input_size, font=('Helvetica', 10))],
        [sg.Text("SĐT Khách Hàng", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="rent_customer_phone", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Ngày Bắt Đầu (YYYY-MM-DD)", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="rent_start_date", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Ngày Kết Thúc (YYYY-MM-DD)", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="rent_end_date", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Giá Thuê", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="rent_price", size=input_size, font=('Helvetica', 10))],
        [sg.Button("Xác Nhận Cho Thuê", size=button_size, font=('Helvetica', 10), button_color=('white', '#ffc107'))],
        [sg.Table(values=[],
                  headings=["Tên Máy", "Khách Hàng", "SĐT", "Ngày Bắt Đầu", "Ngày Kết Thúc", "Giá Thuê", "Ngày Trả", "Counter Trả"],
                  key='rental_table',
                  auto_size_columns=False, col_widths=[20, 15, 15, 15, 15, 15, 15, 15],
                  justification='center', num_rows=10, row_height=30, font=('Helvetica', 10),
                  header_font=('Helvetica', 10, 'bold'), expand_x=True)]
    ]

    return_machine_content = [
        [sg.Text("Tên Máy", size=label_size, font=('Helvetica', 10)),
         sg.Text("", key="return_machine_name", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Tên Khách Hàng Thuê", size=label_size, font=('Helvetica', 10)),
         sg.Text("", key="return_customer_name_display", size=input_size, font=('Helvetica', 10))],
        [sg.Text("SĐT Khách Hàng Thuê", size=label_size, font=('Helvetica', 10)),
         sg.Text("", key="return_customer_phone_display", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Ngày Bắt Đầu", size=label_size, font=('Helvetica', 10)),
         sg.Text("", key="return_start_date", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Ngày Kết Thúc", size=label_size, font=('Helvetica', 10)),
         sg.Text("", key="return_end_date", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Giá Thuê", size=label_size, font=('Helvetica', 10)),
         sg.Text("", key="return_rental_price", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Tên Khách Hàng Trả", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="return_customer_name_input", size=input_size, font=('Helvetica', 10))],
        [sg.Text("SĐT Khách Hàng Trả", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="return_customer_phone_input", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Ngày Trả (YYYY-MM-DD)", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="return_date", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Số Counter Trả", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="return_counter", size=input_size, font=('Helvetica', 10))],
        [sg.Button("Xác Nhận Trả Máy", size=button_size, font=('Helvetica', 10), button_color=('white', '#28a745'))],
        [sg.Table(values=[],
                  headings=["Tên Máy", "Khách Hàng Thuê", "SĐT Thuê", "Ngày Bắt Đầu", "Ngày Kết Thúc", "Giá Thuê",
                            "Ngày Trả", "Counter Trả", "Khách Hàng Trả", "SĐT Trả"],
                  key='rental_table_return',
                  enable_events=True, auto_size_columns=False, col_widths=[20, 15, 15, 15, 15, 15, 15, 15, 15, 15],
                  justification='center', num_rows=10, row_height=30, font=('Helvetica', 10),
                  header_font=('Helvetica', 10, 'bold'), expand_x=True)]
    ]

    maintenance_content = [
        [sg.Text("Mô Tả Bảo Trì", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="maintenance_desc", size=input_size, font=('Helvetica', 10))],
        [sg.Text("Chi Phí (VND)", size=label_size, font=('Helvetica', 10)),
         sg.Input(key="maintenance_cost", size=input_size, font=('Helvetica', 10))],
        [sg.Button("Xác Nhận Bảo Trì", size=button_size, font=('Helvetica', 10), button_color=('white', '#28a745'))],
        [sg.Table(values=[],
                  headings=["Tên Máy", "Ngày Bảo Trì", "Mô Tả", "Chi Phí"],
                  key="maintenance_table",
                  auto_size_columns=False, col_widths=[20, 15, 30, 15],
                  justification='center', num_rows=10, row_height=30, font=('Helvetica', 10),
                  header_font=('Helvetica', 10, 'bold'), expand_x=True)]
    ]

    photocopy_tab = [
        [sg.Frame("Điều Hướng", photocopy_nav, font=('Helvetica', 11, 'bold'), expand_x=True)],
        [sg.Column(machines_list_content, key='machines_list', visible=True, expand_x=True, expand_y=True),
         sg.Column(import_machine_content, key='import_machine', visible=False, expand_x=True, expand_y=True),
         sg.Column(sell_machine_content, key='sell_machine', visible=False, expand_x=True, expand_y=True),
         sg.Column(rent_machine_content, key='rent_machine', visible=False, expand_x=True, expand_y=True),
         sg.Column(return_machine_content, key='return_machine', visible=False, expand_x=True, expand_y=True),
         sg.Column(maintenance_content, key='maintenance', visible=False, expand_x=True, expand_y=True)]
    ]

    control_column = [
        [sg.Button("Thống Kê", size=button_size, font=('Helvetica', 10), button_color=('white', '#6c757d'))],
        [sg.Button("Xuất Excel", size=button_size, font=('Helvetica', 10), button_color=('white', '#6c757d'))],
        [sg.Button("Xuất Lịch Sử", size=button_size, font=('Helvetica', 10), button_color=('white', '#6c757d'))],
        [sg.Button("Xóa Toàn Bộ Dữ Liệu", size=button_size, font=('Helvetica', 10), button_color=('white', '#dc3545'))],
        [sg.Button("Làm Mới", size=button_size, font=('Helvetica', 10), button_color=('white', '#17a2b8'))],
        [sg.Button("Thoát", size=button_size, font=('Helvetica', 10), button_color=('white', '#dc3545'))]
    ]

    layout = [
        [sg.Text("QUẢN LÝ KHO", font=("Helvetica", 25, 'bold'), justification='center', size=(55, 1),
                 pad=((0, 0), (10, 20)))],
        [sg.Column(control_column, vertical_alignment='top', pad=(10, 10)),
         sg.TabGroup([
            [sg.Tab('Quản Lý Vật Tư', vat_tu_tab, font=('Helvetica', 12))],
            [sg.Tab('Quản Lý Máy Photocopy', photocopy_tab, font=('Helvetica', 12))]
        ], key='TabGroup', tab_location='topleft', expand_x=True, expand_y=True)]
    ]

    return layout