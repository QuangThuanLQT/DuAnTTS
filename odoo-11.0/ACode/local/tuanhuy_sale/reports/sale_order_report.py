from odoo import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import cStringIO
import base64
import StringIO
import xlsxwriter
from datetime import datetime


class sale_order_report(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def print_excel(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Phieu Xuat Kho Ban hang')
        bold = workbook.add_format({'bold': True})
        merge_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': '16'})
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'left', 'valign': 'vcenter'})
        back_color = 'C2:E2'
        back_color_date = 'C3:E3'
        string_header = "PHIẾU XUẤT KHO BÁN HÀNG" if not self.sale_order_return else "PHIẾU NHẬP KHO TRẢ HÀNG"
        worksheet.merge_range(back_color, unicode(string_header, "utf-8"), merge_format)
        date = datetime.strptime(self.confirmation_date, DEFAULT_SERVER_DATETIME_FORMAT)
        string = "Ngày %s tháng %s năm %s" % (date.day, date.month, date.year)
        worksheet.merge_range(back_color_date, unicode(string, "utf-8"), header_bold_color)

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 50)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 15)

        row = 7
        count = 0
        summary_header = ['STT', 'Mã hàng', 'Tên hàng', 'Đơn vị', 'Số lượng', 'Đơn giá', 'Thành tiền']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]
        no = 0
        for line in self.order_line:
            no += 1
            row += 1
            count += 1
            worksheet.write(row, 0, no, body_bold_color)
            worksheet.write(row, 1, line.product_id.default_code, body_bold_color)
            worksheet.write(row, 2, line.product_id.name, body_bold_color)
            worksheet.write(row, 3, line.product_uom.name, body_bold_color)
            worksheet.write(row, 4, line.product_uom_qty, body_bold_color)
            worksheet.write(row, 5, line.final_price, body_bold_color)
            worksheet.write(row, 6, line.price_subtotal, body_bold_color)
        row += 1
        worksheet.write(row, 0, unicode("Cộng", "utf-8"), body_bold_color)
        worksheet.write(row, 6, self.amount_untaxed, body_bold_color)
        row += 1
        worksheet.write(row, 0, unicode("Cộng tiền hàng", "utf-8"), body_bold_color)
        worksheet.write(row, 6, self.amount_untaxed, body_bold_color)
        row += 1
        worksheet.write(row, 0, unicode("Thuế suất GTGT", "utf-8"), body_bold_color)
        worksheet.write(row, 3, unicode("Tiền suất GTGT", "utf-8"), body_bold_color)
        worksheet.write(row, 6, self.amount_tax, body_bold_color)
        row += 1
        worksheet.write(row, 3, unicode("Tổng thanh toán", "utf-8"), body_bold_color)
        worksheet.write(row, 6, self.amount_total, body_bold_color)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'DonHangExcel.xlsx', 'datas_fname': 'DonHangExcel.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}