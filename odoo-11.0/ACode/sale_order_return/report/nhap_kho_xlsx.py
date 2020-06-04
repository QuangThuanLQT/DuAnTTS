from odoo import models, fields, api


class NhapKHoXlsx(models.AbstractModel):
    _name = 'report.sale_order_return.report_excel_nhap_kho'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, worksheet, data):
        print("lines", self, data, worksheet)
        worksheet = workbook.add_worksheet('Excel nhập kho')
        merge_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': '16'})
        header_bold_color = workbook.add_format({
            'bold': True,
            'font_size': '14',
            'align': 'center',
            'valign': 'vcenter'
        })
        header_bold_border_color = workbook.add_format({
            'bold': True,
            'font_size': '14',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        body_bold_color = workbook.add_format({
            'bold': False,
            'font_size': '14',
            'align': 'left',
            'valign': 'vcenter'
        })
        body_bold_center_color = workbook.add_format({
            'bold': False,
            'font_size': '14',
            'align': 'center',
            'valign': 'vcenter'
        })
        body_bold_border_color = workbook.add_format({
            'bold': False,
            'font_size': '14',
            'align': 'left',
            'valign': 'vcenter',
            'border': 1
        })
        money = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
        })

        worksheet.merge_range('A1:D1', 'Thể Thao Sỉ', body_bold_color)
        worksheet.merge_range('A2:D2', '435 Hoàng Văn Thụ', body_bold_color)

        worksheet.merge_range('C3:E3', 'BÁO GIÁ', merge_format)
        worksheet.merge_range('C4:E4', 'Ngày ... tháng ... năm ...', header_bold_color)

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 20)

        worksheet.merge_range('A5:F5', 'Người mua:', body_bold_color)
        worksheet.merge_range('A6:F6', 'Tên khách hàng: ...', body_bold_color)
        worksheet.merge_range('A7:F7', 'Địa chỉ: ...', body_bold_color)
        worksheet.merge_range('A8:F8', 'Diễn giải: ...',
                              body_bold_color)
        worksheet.merge_range('A9:F9', 'Điện thoại: ...', body_bold_color)

        worksheet.write(4, 6, 'Số: ...', body_bold_color)
        worksheet.write(5, 6, 'Loại tiền: VND', body_bold_color)

        worksheet.write(10, 0, 'STT', header_bold_border_color)
        worksheet.write(10, 1, 'Mã hàng', header_bold_border_color)
        worksheet.write(10, 2, 'Tên hàng', header_bold_border_color)
        worksheet.write(10, 3, 'Đơn vị', header_bold_border_color)
        worksheet.write(10, 4, 'Số lượng', header_bold_border_color)
        worksheet.write(10, 5, 'Số lượng', header_bold_border_color)
        worksheet.write(10, 6, 'Thành tiền', header_bold_border_color)

        worksheet.write(11, 0, '...', header_bold_border_color)
        worksheet.write(11, 1, '...', header_bold_border_color)
        worksheet.write(11, 2, '...', header_bold_border_color)
        worksheet.write(11, 3, '...', header_bold_border_color)
        worksheet.write(11, 4, '...', header_bold_border_color)
        worksheet.write(11, 5, '...', header_bold_border_color)
        worksheet.write(11, 6, '...', header_bold_border_color)

        worksheet.merge_range('A13:F13', 'Cộng', body_bold_border_color)
        worksheet.merge_range('A14:F14', 'Cộng tiền hàng', body_bold_border_color)
        worksheet.merge_range('A15:B15', 'Thuế suất GTGT', body_bold_border_color)
        worksheet.write(14, 2, '...', body_bold_border_color)
        worksheet.merge_range('D15:F15', 'Tiền suất GTGT', body_bold_border_color)
        worksheet.merge_range('D16:F16', 'Tổng thanh toán', body_bold_border_color)

        worksheet.write(12, 6, '...', body_bold_border_color)
        worksheet.write(13, 6, '...', body_bold_border_color)
        worksheet.write(14, 6, '...', body_bold_border_color)
        worksheet.write(15, 6, '...', body_bold_border_color)

        worksheet.merge_range('A17:G17', 'Số tiền viết bằng chữ: ... đồng.', body_bold_color)
        worksheet.merge_range('E18:G18', 'Ngày ... tháng ... năm ...', body_bold_center_color)

        worksheet.merge_range('A20:B20', 'Người nhận hàng', header_bold_color)
        worksheet.write(19, 2, 'Kho', header_bold_color)
        worksheet.merge_range('D20:E20', 'Người lập phiếu', header_bold_color)
        worksheet.merge_range('F20:G20', 'Giám đốc', header_bold_color)

        worksheet.merge_range('A21:B21', '(Ký, họ tên)', body_bold_center_color)
        worksheet.write(20, 2, '(Ký, họ tên)', body_bold_center_color)
        worksheet.merge_range('D21:E21', '(Ký, họ tên)', body_bold_center_color)
        worksheet.merge_range('F21:G21', '(Ký, họ tên)', body_bold_center_color)
