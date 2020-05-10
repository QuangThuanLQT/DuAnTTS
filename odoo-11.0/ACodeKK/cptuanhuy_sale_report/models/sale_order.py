# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import base64
from xlrd import open_workbook
import StringIO
import xlsxwriter
from datetime import datetime
import pytz

class sale_order_report_popup(models.TransientModel):
    _name = 'sale.order.report.poup'

    date_start      = fields.Date('Thời gian bắt đầu')
    date_end        = fields.Date('Thời gian kết thúc')

    @api.multi
    def do_print(self):
        order_ids = False
        if self.date_start and self.date_end:
            order_ids = self.env['account.move.line'].sudo().search([('sale_id','!=',False),('date','>=',self.date_start),('date','<=',self.date_end)]).mapped('sale_id')
        elif not self.date_start and self.date_end:
            order_ids = self.env['account.move.line'].sudo().search([('sale_id', '!=', False),('date', '<=', self.date_end)]).mapped('sale_id')
        elif self.date_start and not self.date_end:
            order_ids = self.env['account.move.line'].sudo().search([('sale_id', '!=', False), ('date', '>=', self.date_start)]).mapped('sale_id')
        elif not self.date_start and not self.date_end:
            order_ids = self.env['account.move.line'].sudo().search([('sale_id', '!=', False)]).mapped('sale_id')

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Sheet1')

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 10)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 10)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:K', 15)
        worksheet.set_column('L:L', 15)
        worksheet.set_column('M:M', 15)
        worksheet.set_column('N:N', 15)
        worksheet.set_column('O:O', 15)
        worksheet.set_column('R:R', 15)
        worksheet.set_column('P:P', 15)
        worksheet.set_column('Q:Q', 15)
        worksheet.set_column('S:S', 15)
        worksheet.set_column('T:T', 20)
        worksheet.set_column('U:U', 15)

        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.merge_range('A1:U1', 'BÁO CÁO HIỆU QUẢ KINH DOANH', header_bold_color)
        worksheet.merge_range('A2:U2', (self.date_start and datetime.strptime(self.date_start,DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y') or '') + ' - ' + (self.date_end and datetime.strptime(self.date_end,DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y') or ''), header_bold_color)

        row = 4

        summary_header = ['STT','Đơn hàng','Loại đơn hàng','Số hợp đồng','Đối tác','Ngày đặt hàng','Ngày giao hàng thực tế','Doanh thu dự kiến, ban đầu','(1)Doanh thu thực','(2)Giá vốn hàng bán','Lợi nhuận gộp về bán hàng',
                          'Doanh thu hoạt động tài chính','Chi phí tài chính','Chi phí quản lý doanh nghiệp','Chi phí bán hàng','Lợi nhuận thuần từ HĐKD','Thu nhập khác','Chi phí khác','Lợi nhuận khác','Tổng lợi nhuận trước thuế',
                          'Thuế TNDN','Lợi nhuận sau thuế','% tỉ suất lợi nhuận']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        A_total = 0
        B_total = 0
        H_total = 0
        M_total = 0
        O_total = 0

        count = 0
        for line in order_ids:
            count += 1
            row += 1
            local = pytz.timezone(self.env.user.tz or 'Asia/Ho_Chi_Minh')
            covert_date_order = False
            if line.date_order:
                date_order = datetime.strptime(line.date_order, DEFAULT_SERVER_DATETIME_FORMAT)
                covert_date_order = pytz.utc.localize(date_order).astimezone(local).strftime('%d/%m/%Y %H:%M')
            worksheet.write(row, 0, count,text_style)
            worksheet.write(row, 1, line.name or '', text_style)
            worksheet.write(row, 2, line.so_type_id.name or '', text_style)
            worksheet.write(row, 3, line.contract_id.name or '', text_style)
            worksheet.write(row, 4, line.partner_id.name or '', text_style)
            worksheet.write(row, 5, covert_date_order or '', text_style)
            worksheet.write(row, 6, line.validity_date and datetime.strptime(line.validity_date,DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y') or '', text_style)
            worksheet.write(row, 7, '')
            worksheet.write(row, 8, sum(line.move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('511')).mapped('credit')) or '', body_bold_color_number)
            # (1)Doanh thu thực
            A_amount    = sum(line.move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('511')).mapped('credit')) or 0
            A_total += A_amount
            # (2)Giá vốn hàng bán
            worksheet.write(row, 9, sum(line.move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('632')).mapped('debit')) or '', body_bold_color_number)
            B_amount    = sum(line.move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('632')).mapped('debit')) or 0
            B_total += B_amount
            # Lợi nhuận gộp về bán hàng
            worksheet.write(row, 10, A_amount - B_amount, body_bold_color_number)
            # Doanh thu hoạt động tài chính
            worksheet.write(row, 11, sum(line.move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('515')).mapped('credit')) or '', body_bold_color_number)
            D_amount = sum(line.move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('515')).mapped('credit')) or 0
            # Chi phí tài chính
            worksheet.write(row, 12, sum(line.move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('635')).mapped('debit')) or '', body_bold_color_number)
            E_amount = sum(line.move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('635')).mapped('debit')) or 0
            # Chi phí quản lý doanh nghiệp
            worksheet.write(row, 13, sum(line.move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('642')).mapped('debit')) or '', body_bold_color_number)
            # Chi phí bán hàng
            worksheet.write(row, 14, sum(line.move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('641')).mapped('debit')) or '',body_bold_color_number)
            # Lợi nhuận thuần từ HĐKD
            worksheet.write(row, 15, A_amount - B_amount + D_amount - E_amount, body_bold_color_number)
            # Thu nhập khác
            worksheet.write(row, 16, sum(line.move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('711')).mapped('credit')) or '', body_bold_color_number)
            H_amount = sum(line.move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('711')).mapped('credit')) or 0
            H_total += H_amount
            # Chi phí khác
            worksheet.write(row, 17, sum(line.move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('811')).mapped('debit')) or '', body_bold_color_number)
            M_amount = sum(line.move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('811')).mapped('debit')) or 0
            M_total += M_amount
            # Lợi nhuận khác
            worksheet.write(row, 18, '', body_bold_color_number)
            # Tổng lợi nhuận trước thuế
            worksheet.write(row, 19, '', body_bold_color_number)
            # Thuế TNDN
            worksheet.write(row, 20, sum(line.move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('3334')).mapped('credit')) or '', body_bold_color_number)
            # Lợi nhuận sau thuế
            worksheet.write(row, 21, '', body_bold_color_number)
            # % tỉ suất lợi nhuận
            worksheet.write(row, 22, '', body_bold_color_number)

        worksheet.write(2, 7, 'Tổng', body_bold_color)
        worksheet.write(2, 8, 'Tổng %s'%A_total, body_bold_color)
        worksheet.write(2, 9, 'Tổng %s'%B_total, body_bold_color)
        worksheet.write(2, 16, 'Tổng %s'%H_total, body_bold_color)
        worksheet.write(2, 17, 'Tổng %s'%M_total, body_bold_color)
        worksheet.write(2, 19, 'Tổng', body_bold_color)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': 'SaleReport.xlsx',
            'datas_fname': 'SaleReport.xlsx',
            'datas': result
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
        }

class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def theo_doi_sale_excel(self):
        order_ids = self
        if self._context.get('active_ids',False) and self._context.get('active_model') == 'sale.order':
            order_ids = self.browse(self._context.get('active_ids',False))
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        string_sheet = 'Theo dõi đơn hàng'
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
        # back_color =
        # back_color_date =

        worksheet.set_column('A:A', 7)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 30)
        worksheet.set_column('F:F', 30)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 20)


        row = 0
        count = 0
        summary_header = ['STT', 'Số Job', 'Ngày đặt hàng', 'Ngày giao hàng', 'Khách hàng', 'Diễn giải', 'Tổng giá trị', 'Ngày hoàn thành']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_border_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
        no = 0
        local = pytz.timezone(self.env.user.tz or 'Asia/Ho_Chi_Minh')
        for line in order_ids:
            no += 1
            row += 1
            count += 1
            covert_date_order = covert_confirmation_date = validity_date = False
            if line.date_order:
                date_order = datetime.strptime(line.date_order, DEFAULT_SERVER_DATETIME_FORMAT)
                covert_date_order = pytz.utc.localize(date_order).astimezone(local).strftime('%d/%m/%Y %H:%M')
            if line.confirmation_date:
                confirmation_date = datetime.strptime(line.confirmation_date, DEFAULT_SERVER_DATETIME_FORMAT)
                covert_confirmation_date = pytz.utc.localize(confirmation_date).astimezone(local).strftime('%d/%m/%Y %H:%M')
            if line.validity_date:
                validity_date = datetime.strptime(line.validity_date, DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y')
            worksheet.write(row, 0, no)
            worksheet.write(row, 1, line.name)
            worksheet.write(row, 2, covert_date_order or '')
            worksheet.write(row, 3, line.validity_date)
            worksheet.write(row, 4, line.partner_id.display_name or '')
            worksheet.write(row, 5, line.note)
            worksheet.write(row, 6, line.amount_total, money)
            worksheet.write(row, 7, covert_confirmation_date or '')
        row += 1

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'TheoDoiDonHangExcel.xlsx', 'datas_fname': 'TheoDoiDonHangExcel.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}