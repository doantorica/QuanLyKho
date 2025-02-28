import PySimpleGUI as sg

def show_vat_tu_stats_window(inventory_manager):
    stats = inventory_manager.get_detailed_sales_stats()
    if not stats:
        sg.popup("Không có dữ liệu bán hàng để thống kê!", title="Thông báo", font=('Helvetica', 12))
        return
    formatted_stats = [[row[0], row[1], f"{row[2] or 0:,.2f} VND", f"{row[3] or 0:,.2f} VND"] for row in stats]
    layout = [
        [sg.Text("Thống Kê Doanh Thu & Lợi Nhuận Vật Tư", font=('Helvetica', 16, 'bold'), justification='center')],
        [sg.Table(values=formatted_stats,
                  headings=["Loại", "Số Lượng Bán", "Doanh Thu", "Lợi Nhuận"],
                  auto_size_columns=False,
                  col_widths=[25, 15, 20, 20],
                  justification='center',
                  num_rows=min(15, len(formatted_stats)),
                  font=('Helvetica', 10),
                  header_font=('Helvetica', 10, 'bold'),
                  expand_x=True)],
        [sg.Button("Đóng", size=(10, 1))]
    ]
    window = sg.Window("Thống Kê Chi Tiết Vật Tư", layout, size=(700, 400), resizable=True, finalize=True)
    while True:
        event, _ = window.read()
        if event in (sg.WIN_CLOSED, "Đóng"):
            break
    window.close()

def show_photocopy_detailed_stats_window(inventory_manager):
    stats = inventory_manager.get_detailed_photocopy_stats()
    if not stats:
        sg.popup("Không có dữ liệu để thống kê!", title="Thông báo", font=('Helvetica', 12))
        return
    formatted_stats = [[row[0], row[1], f"{row[2] or 0:,.2f} VND", f"{row[3] or 0:,.2f} VND"] for row in stats]
    layout = [
        [sg.Text("Thống Kê Doanh Thu & Lợi Nhuận Máy Photocopy", font=('Helvetica', 16, 'bold'), justification='center')],
        [sg.Table(values=formatted_stats,
                  headings=["Loại", "Số Lượng", "Doanh Thu", "Lợi Nhuận"],
                  auto_size_columns=False,
                  col_widths=[25, 15, 20, 20],
                  justification='center',
                  num_rows=min(15, len(formatted_stats)),
                  font=('Helvetica', 10),
                  header_font=('Helvetica', 10, 'bold'),
                  expand_x=True)],
        [sg.Button("Đóng", size=(10, 1))]
    ]
    window = sg.Window("Thống Kê Chi Tiết Máy Photocopy", layout, size=(700, 400), resizable=True, finalize=True)
    while True:
        event, _ = window.read()
        if event in (sg.WIN_CLOSED, "Đóng"):
            break
    window.close()