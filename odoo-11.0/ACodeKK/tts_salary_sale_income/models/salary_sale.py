# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import StringIO
import xlsxwriter
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from odoo.exceptions import UserError

class tts_salary_delivery_income(models.Model):
    _name = 'salary.sale.income'

    default_code = fields.Char(readonly=True)
    month = fields.Char(readonly=True)
    user = fields.Many2one('res.users')
    doanh_so_ban_hang = fields.Float(digits=(16, 0), readonly=True)
    tong_tra_hang = fields.Float(digits=(16, 0), readonly=True)
    thuong_ban_hang = fields.Float(digits=(16, 0), readonly=True)
    tru_tra_hang = fields.Float(digits=(16, 0), readonly=True)
    luong_ngay_cong = fields.Float(digits=(16, 0))
    thuong_khac = fields.Float(digits=(16, 0))
    tru_ung_luong = fields.Float(digits=(16, 0))
    thu_nhap = fields.Float(digits=(16, 0),compute='get_thu_nhap_bh', readonly=True)
    ghi_chu = fields.Text()
    thang = fields.Char(readonly=True)
    nam = fields.Char(readonly=True)


    @api.multi
    def get_thu_nhap_bh(self):
        for rec in self:
            rec.thu_nhap = rec.thuong_ban_hang - rec.tru_tra_hang + rec.luong_ngay_cong + rec.thuong_khac - rec.tru_ung_luong

    def _get_datetime_utc(self, datetime_val):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(datetime_val, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime(
            '%d/%m/%Y %H:%M')
        return resuft

    @api.model
    def export_overview_salary_sale(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        thang = self.env['salary.sale.income'].search(domain, limit=1).thang
        nam = self.env['salary.sale.income'].search(domain, limit=1).nam
        sale_ids = self.env['sale.income'].search([('time_hd', 'ilike', '%' + nam + '-' + thang + '%')])

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Thông tin chi tiết')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')
        header_bold_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        header_bold_number.set_num_format('#,##0')
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})

        worksheet.set_column('A:A', 19)
        worksheet.set_column('B:B', 14)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 13)
        worksheet.set_column('E:E', 17)
        worksheet.set_column('F:F', 13)
        worksheet.set_column('G:G', 10)

        summary_header = ['Nhân viên bán hàng', 'Đơn hàng', 'Khách hàng', 'Số hoá đơn', 'Thời gian tạo hoá đơn', 'Giá trị đơn hàng', 'Thu nhập']

        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for rec in sale_ids:
            row += 1

            worksheet.write(row, 0, rec.user.name or '', text_style)
            worksheet.write(row, 1, rec.don_hang or '', text_style)
            worksheet.write(row, 2, rec.khach_hang or '', text_style)
            worksheet.write(row, 3, rec.hoa_don or '', text_style)
            worksheet.write(row, 4, rec.time_hd or '', text_style)
            worksheet.write(row, 5, '{:,}'.format(int(rec.amount)) or '', text_style)
            worksheet.write(row, 6, '{:,}'.format(int(rec.thu_nhap)) or '', text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()