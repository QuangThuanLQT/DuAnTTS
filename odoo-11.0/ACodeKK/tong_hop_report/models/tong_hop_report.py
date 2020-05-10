# -*- coding: utf-8 -*-

from odoo import models, fields, api
# import re
import base64
import StringIO
import xlsxwriter
from odoo.tools.misc import formatLang
import math
from odoo.tools.float_utils import float_compare


import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class tong_hop_report(models.TransientModel):
    _name = 'tong.hop.report'

    account_id       = fields.Many2one('account.account', string='Tài Khoản')
    start_date       = fields.Date(String='Từ Ngày', required=True)
    end_date         = fields.Date(String='Đến Ngày')

    @api.model
    def get_invalid_sale_order(self, force_null=False):
        self.ensure_one()

        conditions = [('state', '=', 'sale'),('sale_order_return', '=', False),('name','not in',['Công ty Cổ Phần Cơ điện Tuấn Huy','Anh Phúc Cơ Điện Tuấn Huy'])]

        if self.start_date:
            conditions.append(('date_order', '>=', self.start_date))
        if self.end_date:
            conditions.append(('date_order', '<=', self.end_date))

        orders = self.env['sale.order'].search(conditions, order='date_order asc')
        return orders

    @api.multi
    def print_excel(self,context=False,response=False):
        self.ensure_one()

        if self.account_id and self.account_id.code == '131':
            order_ids = self.get_invalid_sale_order()
            no_invoice_orders = order_ids.filtered(lambda x: not x.invoice_ids.filtered(lambda inv: inv.state != 'cancel') and x.amount_total != 0)
            invalid_invoice_orders = order_ids.filtered(lambda x: x.invoice_ids and float_compare(x.amount_total, sum(x.invoice_ids.filtered(lambda x: x.state != 'cancel').mapped('amount_total')), 0) != 0)
            if (no_invoice_orders or invalid_invoice_orders) and not response:
                return {
                    'name': 'Hoá đơn không hợp lệ',
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.order.no.invoice',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'no_invoice_order_ids': no_invoice_orders.mapped('id'),
                        'invalid_order_line_ids': invalid_invoice_orders.mapped('id'),
                    },
                }

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        worksheet = workbook.add_worksheet('Báo cáo tổng hợp')
        data = self.get_data_report()
        self.write_data_to_sheet(workbook, worksheet, data)

        workbook.close()
        output.seek(0)
        if response:
            response.stream.write(output.read())
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': 'TongHopExcel.xlsx',
            'datas_fname': 'TongHopExcel.xlsx',
            'datas': result
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
        }

    @api.model
    def get_data_report(self):
        self.ensure_one()

        data = {
            'ids': self.ids,
            'model': 'tong.hop.report',
        }

        data_line_report = []

        sum_no_before = 0
        sum_co_before = 0
        sum_no_current = 0
        sum_co_current = 0
        sum_no_end = 0
        sum_co_end = 0

        query_string = "SELECT DISTINCT partner_id FROM account_move_line WHERE account_id = %s ORDER BY partner_id" % (self.account_id.id)
        self.env.cr.execute(query_string)
        lines = self.env.cr.fetchall()

        for line in lines:
            line_data = {'partner_ref': '', 'partner_name': ''}
            conditions = [('account_id', '=', self.account_id.id)]
            conditions_before = [('account_id', '=', self.account_id.id)]

            if self.start_date:
                conditions.append(('date', '>=', self.start_date))
                conditions_before.append(('date', '<', self.start_date))
            if self.end_date:
                conditions.append(('date', '<=', self.end_date))
            else:
                self.end_date = fields.Date.today()
                conditions.append(('date', '<=', self.end_date))

            partner_id = line[0] or False
            if partner_id:
                partner = self.env['res.partner'].browse(partner_id)
                conditions.append(('partner_id', '=', partner.id))
                conditions_before.append(('partner_id', '=', partner.id))
                line_data.update({
                    'partner_ref': partner.ref or partner.id,
                    'partner_name': partner.name,
                })
            else:
                conditions.append(('partner_id', '=', False))
                conditions_before.append(('partner_id', '=', False))

            no_before = 0.0
            co_before = 0.0
            if self.start_date:
                data_before = self.env['account.move.line'].search(conditions_before)
                for data_line in data_before:
                    no_before += data_line.debit
                    co_before += data_line.credit

            no_before = self.round_number(no_before)
            co_before = self.round_number(co_before)

            no_current = 0.0
            co_current = 0.0
            current_data = self.env['account.move.line'].search(conditions)  # , order='partner_id asc, date asc'
            for data_line in current_data:
                no_current += data_line.debit
                co_current += data_line.credit

            no_current = self.round_number(no_current)
            co_current = self.round_number(co_current)

            no_end = 0.0
            co_end = 0.0
            sum_cong_no = no_before + no_current - co_before - co_current
            if sum_cong_no < 0:
                co_end = - sum_cong_no
            else:
                no_end = sum_cong_no

            no_end = self.round_number(no_end)
            co_end = self.round_number(co_end)
            sum_no_before += no_before
            sum_co_before += co_before
            sum_no_current += no_current
            sum_co_current += co_current
            sum_no_end += no_end
            sum_co_end += co_end

            line_data.update({
                'account'    : self.account_id.code,
                'no_before'  : no_before,
                'co_before'  : co_before,
                'no_current' : no_current,
                'co_current' : co_current,
                'no_end'     : no_end,
                'co_end'     : co_end,
            })
            data_line_report.append(line_data)
        sum = {
            'sum_no_before': sum_no_before,
            'sum_co_before': sum_co_before,
            'sum_no_current': sum_no_current,
            'sum_co_current': sum_co_current,
            'sum_no_end': sum_no_end,
            'sum_co_end': sum_co_end
        }
        return {
            'data_line_report': data_line_report,
            'sum': sum
        }

    def round_number(self, number):
        return number
        # return math.floor(number / 100) * 100

    def write_data_to_sheet(self, workbook, worksheet, data, show_header=True):

        # merge_format = workbook.add_format({
        #     'bold': True,
        #     'align': 'center',
        #     'valign': 'vcenter',
        #     'font_size': '16'
        # })
        border_format = workbook.add_format({
            'border': 1
        })
        header_bold_color = workbook.add_format({
            'bold': True,
            'font_size': '16',
            'align': 'center',
            'valign': 'vcenter',

        })
        header_color = workbook.add_format({
            'bold': True,
            'font_size': '14',
            'align': 'left',
            'valign': 'vcenter',
        })
        body_bold_color = workbook.add_format({
            'bold': False,
            'border': 1,
            'font_size': '14',
            'align': 'left',
            'valign': 'vcenter',
            'bg_color': 'dddddd',
        })
        money = workbook.add_format({'num_format': '#,##0', 'border': 1})

        money2 = workbook.add_format({'num_format': '#,##0', 'border': 1, 'bold': True,})

        if show_header:
            worksheet.set_column('A:A', 60)
            worksheet.set_column('B:B', 8)
            worksheet.set_column('C:C', 15)
            worksheet.set_column('D:D', 15)
            worksheet.set_column('E:E', 15)
            worksheet.set_column('F:F', 15)
            worksheet.set_column('G:G', 15)
            worksheet.set_column('H:H', 15)
            worksheet.set_column('I:I', 15)

            worksheet.merge_range('A1:I1', "TỔNG HỢP %s" %(self.account_id.display_name,), header_bold_color)
            worksheet.merge_range('A2:F2', "Kỳ báo cáo:", header_color)
            worksheet.write(1, 6, self.start_date, header_color)
            worksheet.write(1, 7, self.end_date, header_color)

            # worksheet.merge_range('A4:A5', "Mã khách hàng", body_bold_color)
            worksheet.merge_range('A6:A7', "Tên khách hàng", body_bold_color)
            worksheet.merge_range('B6:B7', "TK", body_bold_color)
            worksheet.merge_range('C6:D6', "Số dư đầu kỳ", body_bold_color)
            worksheet.merge_range('E6:F6', "Số phát sinh", body_bold_color)
            worksheet.merge_range('G6:H6', "Số dư cuối kỳ", body_bold_color)
            worksheet.write(6, 2, "Nợ", body_bold_color)
            worksheet.write(6, 3, "Có", body_bold_color)
            worksheet.write(6, 4, "Nợ", body_bold_color)
            worksheet.write(6, 5, "Có", body_bold_color)
            worksheet.write(6, 6, "Nợ", body_bold_color)
            worksheet.write(6, 7, "Có", body_bold_color)
        row_sum = 3
        line = data['sum']
        worksheet.write(row_sum, 2, line['sum_no_before'], money2)
        worksheet.write(row_sum, 3, line['sum_co_before'], money2)
        worksheet.write(row_sum, 4, line['sum_no_current'], money2)
        worksheet.write(row_sum, 5, line['sum_co_current'], money2)
        worksheet.write(row_sum, 6, line['sum_no_end'], money2)
        worksheet.write(row_sum, 7, line['sum_co_end'], money2)
        row = 7
        for line in data['data_line_report']:
            # worksheet.write(row, 0, line['partner_ref'], border_format)
            worksheet.write(row, 0, line['partner_name'], border_format)
            worksheet.write(row, 1, line['account'], border_format)
            worksheet.write(row, 2, line['no_before'], money)
            worksheet.write(row, 3, line['co_before'], money)
            worksheet.write(row, 4, line['no_current'], money)
            worksheet.write(row, 5, line['co_current'], money)
            worksheet.write(row, 6, line['no_end'], money)
            worksheet.write(row, 7, line['co_end'], money)
            row += 1

        return True