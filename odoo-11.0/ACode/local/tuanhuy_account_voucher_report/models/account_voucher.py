# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.float_utils import float_is_zero, float_compare
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import StringIO
import xlsxwriter
import base64
from odoo.exceptions import UserError

class account_voucher(models.Model):
    _inherit = 'account.voucher'

    @api.multi
    def print_voucher_excel(self):
        voucher_ids = self.env['account.voucher']
        if self.env.context.get('active_ids',False) and self.env.context.get('active_model',False) == 'account.voucher':
           voucher_ids = self.env['account.voucher'].browse(self.env.context.get('active_ids',False))
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        string_sheet = 'Giấy báo có (Thu)'
        worksheet = workbook.add_worksheet(string_sheet)
        bold = workbook.add_format({'bold': True})

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
            'border': 1,
            'bg_color': '#00BFFF',
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

        worksheet.merge_range('A1:M1', 'BÁO CÁO GIẤY BÁO CÓ (THU)', header_bold_color)
        worksheet.write(1, 4, 'Ngày kết xuất:' , header_bold_color)
        worksheet.write(2, 4, 'Kỳ kết xuất:' , header_bold_color)

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 30)
        worksheet.set_column('E:E', 25)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 35)
        worksheet.set_column('H:H', 10)
        worksheet.set_column('I:I', 15)
        worksheet.set_column('J:J', 15)
        worksheet.set_column('K:K', 20)
        worksheet.set_column('L:L', 10)

        row = 4
        count = 0
        summary_header = ['STT', 'Ngày lập phiếu', 'Số', 'Đối tác', 'Ngân hàng', 'Số Phiếu Thu', 'Diễn giải', 'Tài Khoản', 'Đơn hàng', 'Đơn Mua hàng', 'Tổng', 'Trạng thái']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_border_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
        no = 0
        total = 0

        for line in voucher_ids:
            no += 1
            row += 1
            count += 1
            worksheet.write(row, 0, no, body_bold_border_color)
            worksheet.write(row, 1, line.date and datetime.strptime(line.date, DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y'), body_bold_border_color)
            worksheet.write(row, 2, line.number or '', body_bold_border_color)
            worksheet.write(row, 3, line.partner_id and line.partner_id.name or '', body_bold_border_color)
            worksheet.write(row, 4, line.bank_id and line.bank_id.name, body_bold_border_color)
            worksheet.write(row, 5, line.number_voucher or '', body_bold_border_color)
            worksheet.write(row, 6, line.explain or '', body_bold_border_color)
            worksheet.write(row, 7, line.account_line_id_sub and line.account_line_id_sub.code or '', body_bold_border_color)
            worksheet.write(row, 8, line.sale_ids and ', '.join([sale.name for sale in line.sale_ids]) or '', body_bold_border_color)
            worksheet.write(row, 9, line.purchase_ids and ', '.join([purchase.name for purchase in line.purchase_ids]) or '', body_bold_border_color)
            worksheet.write(row, 10, line.amount, money)
            state =''
            if line.state == 'draft':
                state = 'Bản thảo'
            elif line.state == 'cancel':
                state = 'Đã hủy'
            elif line.state == 'proforma':
                state = 'Hóa đơn tạm'
            elif line.state == 'posted':
                state = 'Đã vào sổ'
            worksheet.write(row, 11, state, body_bold_border_color)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'Giấy báo có (Thu).xlsx', 'datas_fname': 'Giấy báo có (Thu).xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}