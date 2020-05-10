# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
import StringIO
import xlsxwriter
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT


class res_partner_ihr(models.Model):
    _inherit = 'res.partner'

    tax_code = fields.Char(string='Mã số thuế')

    def _get_profile_partner(self, tax_code):
        api_url = "https://thongtindoanhnghiep.co/api/company/%s" % (self.tax_code)
        r = requests.get(api_url, params={})
        result = r.json()
        return result

    @api.onchange('tax_code')
    def onchange_tax_code(self):
        if self.tax_code and not self.id:
            data = self._get_profile_partner(self.tax_code)
            self.ref = data.get('ID',False)
            self.name = data.get('Title', False)
            self.street = data.get('DiaChiCongTy', False)
            self.phone = data.get('NoiDangKyQuanLy_DienThoai', False) or data.get('NoiNopThue_DienThoai', False)

    @api.model
    def print_partner_excel(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        partner_ids = self.env['res.partner'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Customers')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:J', 20)

        summary_header = ['Tên', 'Mã', 'Địa chỉ', 'Trang web', 'Điện thoại',
                          'Di động', 'Mã số thuế', 'Nhóm KH 1', 'Nhóm KH 2',
                        ]
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for partner_id in partner_ids:
            row += 1
            worksheet.write(row, 0, partner_id.display_name)
            worksheet.write(row, 1, partner_id.ref or '')
            worksheet.write(row, 2, partner_id.street or '')
            worksheet.write(row, 3, partner_id.website or '')
            worksheet.write(row, 4, partner_id.phone or '')
            worksheet.write(row, 5, partner_id.mobile or '')
            worksheet.write(row, 6, partner_id.tax_code or '')
            worksheet.write(row, 7, partner_id.group_kh1_id.name or '')
            worksheet.write(row, 8, partner_id.group_kh2_id.name or '')
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
