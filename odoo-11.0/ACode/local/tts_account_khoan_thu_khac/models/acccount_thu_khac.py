# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import StringIO
import xlsxwriter
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class account_khoan_thu_khac(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _get_datetime_utc(self, datetime_val):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(datetime_val, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime(
            '%d/%m/%Y %H:%M:%S')
        return resuft

    @api.model
    def export_overview_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        amount_ids = self.env['sale.order'].search(domain)
        len_data = len(amount_ids)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Overview')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')
        header_bold_number = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'right', 'valign': 'vcenter'})
        header_bold_number.set_num_format('#,##0')


        worksheet.set_column('A:A', 36)
        worksheet.set_column('B:B', 16)
        worksheet.set_column('C:C', 14)
        worksheet.set_column('D:D', 26)
        worksheet.set_column('E:E', 14)
        worksheet.set_column('F:F', 19)
        worksheet.set_column('G:G', 16)
        worksheet.set_column('H:H', 16)

        summary_header = ['Khách hàng', 'Ngày xác nhận', 'Source Document', 'Nhân viên bán hàng', 'Phụ phí giao hàng',
                          'Trả trước phí ship nhà xe', 'Trạng thái đơn hàng', 'Trạng thái hoạt động' ]
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        row += 1
        summary_header_2 = ['E', 'F']
        [worksheet.write(row, header_cell + 4, "=SUM(%s%s:%s%s)" % (summary_header_2[header_cell], row + 2, summary_header_2[header_cell], row + 1 + len_data),header_bold_number)
         for header_cell in range(0, len(summary_header_2)) if summary_header_2[header_cell]]

        for rec in amount_ids:
            row += 1
            state = dict(self.env['sale.order'].fields_get(allfields=['state'])['state']['selection'])
            tt_donhang = dict(self.env['sale.order'].fields_get(allfields=['trang_thai_dh'])['trang_thai_dh']['selection'])
            confirm_date = ''
            if rec.confirmation_date:
                confirm_date = self._get_datetime_utc(rec.confirmation_date)

            worksheet.write(row, 0, rec.partner_id.display_name or '')
            worksheet.write(row, 1, confirm_date or '')
            worksheet.write(row, 2, rec.name or '')
            worksheet.write(row, 3, rec.create_uid.name or '')
            worksheet.write(row, 4, rec.delivery_amount or '')
            worksheet.write(row, 5, rec.transport_amount or '')
            worksheet.write(row, 6, state.get(rec.state))
            worksheet.write(row, 7, tt_donhang.get(rec.trang_thai_dh) or '')
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
