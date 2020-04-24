# -*- coding: utf-8 -*-

from odoo import models, fields, api
# import re
import base64
import StringIO
import xlsxwriter
from odoo.tools.misc import formatLang
import math
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class tong_hop_report(models.TransientModel):
    _name = 'chi.tiet.report'

    partner_id = fields.Many2one('res.partner', 'Khách Hàng')
    start_date = fields.Date(String='Từ Ngày', required=True)
    end_date = fields.Date(String='Đến Ngày')

    def print_excel_report(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        worksheet1 = workbook.add_worksheet('So ban hang')
        sheet1 = self.create_worksheet1(workbook, worksheet1)
        worksheet2 = workbook.add_worksheet('So tra hang ban')
        sheet2 = self.create_worksheet2(workbook, worksheet2)
        worksheet3 = workbook.add_worksheet('So mua hang')
        sheet3 = self.create_worksheet3(workbook, worksheet3)
        worksheet4 = workbook.add_worksheet('So tra hang mua')
        sheet4 = self.create_worksheet4(workbook, worksheet4)
        worksheet5 = workbook.add_worksheet('PhieuThu')
        sheet5 = self.create_worksheet5(workbook, worksheet5)
        worksheet6 = workbook.add_worksheet('PhieuChi')
        sheet6 = self.create_worksheet6(workbook, worksheet6)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'Baocao_ChiTiet_Excel.xlsx', 'datas_fname': 'Baocao_ChiTiet_Excel.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}

    def get_sale_order_data(self,conditions_add=False):

        conditions = [('state', '=', 'sale')]
        if self.start_date:
            conditions.append(('date_order', '>=', self.start_date))
        if self.end_date:
            conditions.append(('date_order', '<=', self.end_date))
        if self.partner_id:
            conditions.append(('partner_id', '=', self.partner_id.id))

        if conditions_add:
            conditions.append(conditions_add)
        sale_order_ids = self.env['sale.order'].search(conditions, order='date_order asc')

        line_data = []
        for sale_order in sale_order_ids:
            line_data.append({
                'date_order': datetime.strptime(sale_order.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                    "%d/%m/%Y"),
                'order_name': sale_order.name,
                'partner_name': sale_order.partner_id.name,
                'amount_untaxed': sale_order.amount_untaxed if conditions_add else -(sale_order.amount_untaxed)
                if sale_order.sale_order_return else sale_order.amount_untaxed,
                'amount_discount': sale_order.amount_discount,
                'amount_tax': sale_order.amount_tax,
                'amount_total': sale_order.amount_total if conditions_add else -(sale_order.amount_total)
                if sale_order.sale_order_return else sale_order.amount_total,
            })

        return line_data
    def get_purchase_order_data(self,conditions_add=False):

        conditions = [('state', '=', 'purchase')]
        if self.start_date:
            conditions.append(('date_order', '>=', self.start_date))
        if self.end_date:
            conditions.append(('date_order', '<=', self.end_date))
        if self.partner_id:
            conditions.append(('partner_id', '=', self.partner_id.id))

        if conditions_add:
            conditions.append(conditions_add)
        sale_order_ids = self.env['purchase.order'].search(conditions, order='date_order asc')

        line_data = []
        for sale_order in sale_order_ids:
            line_data.append({
                'date_order': datetime.strptime(sale_order.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                    "%d/%m/%Y"),
                'order_name': sale_order.name,
                'partner_name': sale_order.partner_id.name,
                'amount_untaxed': sale_order.amount_untaxed if conditions_add else -(sale_order.amount_untaxed)
                if sale_order.sale_order_return else sale_order.amount_untaxed,
                'amount_discount': sale_order.amount_discount,
                'amount_tax': sale_order.amount_tax,
                'amount_total': sale_order.amount_total if conditions_add else -(sale_order.amount_total)
                if sale_order.sale_order_return else sale_order.amount_total,
            })

        return line_data

    def get_account_voucher_data(self,conditions_add=False):

        conditions = [('state', '=', 'posted')]
        if self.start_date:
            conditions.append(('date', '>=', self.start_date))
        if self.end_date:
            conditions.append(('date', '<=', self.end_date))
        if self.partner_id:
            conditions.append(('partner_id', '=', self.partner_id.id))

        if conditions_add:
            conditions.append(conditions_add)
        sale_order_ids = self.env['account.voucher'].search(conditions, order='date asc')

        line_data = []
        for sale_order in sale_order_ids:
            line_data.append({
                'date_order': datetime.strptime(sale_order.date, DEFAULT_SERVER_DATE_FORMAT).strftime(
                    "%d/%m/%Y"),
                'voucher_number': sale_order.number_voucher,
                'partner_name': sale_order.partner_id.name,
                'explain': sale_order.explain_sub,
                'amount': sale_order.amount,

            })

        return line_data

    def create_worksheet1(self, workbook, worksheet):
        merge_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': '16', 'border': 1})
        header1_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0'})
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', 'bg_color': 'cce0ff'})
        footer_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', })
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '12', 'align': 'left', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', })
        back_color = 'A2:I2'
        back_color_date = 'A3:I3'

        worksheet.set_row(1, 25)
        worksheet.set_row(2, 18)
        worksheet.merge_range(back_color, unicode("SỔ BÁN HÀNG", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 60)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        # worksheet3.set_column('G:G', 20)

        row = 4
        summary_header = ['Ngày đặt hàng', 'Số đơn hàng', 'Tên khách hàng', 'Tổng chưa thuế', 'Thuế', 'Tổng tiền']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        sale_order_data = self.get_sale_order_data(('sale_order_return', '=', False))
        sum_amount_untaxed = 0.0
        sum_amount_discount = 0.0
        sum_amount_tax = 0.0
        sum_amount_total = 0.0
        for line_sale_order in sale_order_data:
            row += 1
            worksheet.write(row, 0, line_sale_order.get('date_order', False), body_bold_color)
            worksheet.write(row, 1, line_sale_order.get('order_name', False), body_bold_color)
            worksheet.write(row, 2, line_sale_order.get('partner_name', False), body_bold_color)
            worksheet.write(row, 3, line_sale_order.get('amount_untaxed', False), body_bold_color)
            # worksheet3.write(row, 4, line_sale_order.get('amount_discount', False), body_bold_color)
            worksheet.write(row, 4, line_sale_order.get('amount_tax', False), body_bold_color)
            worksheet.write(row, 5, line_sale_order.get('amount_total', False), body_bold_color)
            sum_amount_untaxed += line_sale_order.get('amount_untaxed', False)
            sum_amount_discount += line_sale_order.get('amount_discount', False)
            sum_amount_tax += line_sale_order.get('amount_tax', False)
            sum_amount_total += line_sale_order.get('amount_total', False)
        row += 1
        worksheet.write(row, 2, "Tổng", footer_bold_color)
        worksheet.write(row, 3, sum_amount_untaxed, footer_bold_color)
        # worksheet3.write(row, 4, sum_amount_discount, header_bold_color)
        worksheet.write(row, 4, sum_amount_tax, footer_bold_color)
        worksheet.write(row, 5, sum_amount_total, footer_bold_color)

    def create_worksheet2(self, workbook, worksheet):
        merge_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': '16', 'border': 1})
        header1_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0'})
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', 'bg_color': 'cce0ff'})
        footer_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', })
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '12', 'align': 'left', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', })
        back_color = 'A2:I2'
        back_color_date = 'A3:I3'

        worksheet.set_row(1, 25)
        worksheet.set_row(2, 18)
        worksheet.merge_range(back_color, unicode("SỔ TRẢ HÀNG BÁN", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 60)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        # worksheet3.set_column('G:G', 20)

        row = 4
        summary_header = ['Ngày đặt hàng', 'Số đơn hàng', 'Tên khách hàng', 'Tổng chưa thuế', 'Thuế', 'Tổng tiền']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        sale_order_data = self.get_sale_order_data(('sale_order_return', '=', True))
        sum_amount_untaxed = 0.0
        sum_amount_discount = 0.0
        sum_amount_tax = 0.0
        sum_amount_total = 0.0
        for line_sale_order in sale_order_data:
            row += 1
            worksheet.write(row, 0, line_sale_order.get('date_order', False), body_bold_color)
            worksheet.write(row, 1, line_sale_order.get('order_name', False), body_bold_color)
            worksheet.write(row, 2, line_sale_order.get('partner_name', False), body_bold_color)
            worksheet.write(row, 3, line_sale_order.get('amount_untaxed', False), body_bold_color)
            # worksheet3.write(row, 4, line_sale_order.get('amount_discount', False), body_bold_color)
            worksheet.write(row, 4, line_sale_order.get('amount_tax', False), body_bold_color)
            worksheet.write(row, 5, line_sale_order.get('amount_total', False), body_bold_color)
            sum_amount_untaxed += line_sale_order.get('amount_untaxed', False)
            sum_amount_discount += line_sale_order.get('amount_discount', False)
            sum_amount_tax += line_sale_order.get('amount_tax', False)
            sum_amount_total += line_sale_order.get('amount_total', False)
        row += 1
        worksheet.write(row, 2, "Tổng", footer_bold_color)
        worksheet.write(row, 3, sum_amount_untaxed, footer_bold_color)
        # worksheet3.write(row, 4, sum_amount_discount, header_bold_color)
        worksheet.write(row, 4, sum_amount_tax, footer_bold_color)
        worksheet.write(row, 5, sum_amount_total, footer_bold_color)

    def create_worksheet3(self, workbook, worksheet):
        merge_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': '16', 'border': 1})
        header1_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0'})
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', 'bg_color': 'cce0ff'})
        footer_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', })
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '12', 'align': 'left', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', })
        back_color = 'A2:I2'
        back_color_date = 'A3:I3'

        worksheet.set_row(1, 25)
        worksheet.set_row(2, 18)
        worksheet.merge_range(back_color, unicode("SỔ MUA HÀNG", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 60)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        # worksheet3.set_column('G:G', 20)

        row = 4
        summary_header = ['Ngày đặt hàng', 'Số đơn hàng', 'Tên khách hàng', 'Tổng chưa thuế', 'Thuế', 'Tổng tiền']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        sale_order_data = self.get_purchase_order_data(('purchase_order_return', '=', False))
        sum_amount_untaxed = 0.0
        sum_amount_discount = 0.0
        sum_amount_tax = 0.0
        sum_amount_total = 0.0
        for line_sale_order in sale_order_data:
            row += 1
            worksheet.write(row, 0, line_sale_order.get('date_order', False), body_bold_color)
            worksheet.write(row, 1, line_sale_order.get('order_name', False), body_bold_color)
            worksheet.write(row, 2, line_sale_order.get('partner_name', False), body_bold_color)
            worksheet.write(row, 3, line_sale_order.get('amount_untaxed', False), body_bold_color)
            # worksheet3.write(row, 4, line_sale_order.get('amount_discount', False), body_bold_color)
            worksheet.write(row, 4, line_sale_order.get('amount_tax', False), body_bold_color)
            worksheet.write(row, 5, line_sale_order.get('amount_total', False), body_bold_color)
            sum_amount_untaxed += line_sale_order.get('amount_untaxed', False)
            sum_amount_discount += line_sale_order.get('amount_discount', False)
            sum_amount_tax += line_sale_order.get('amount_tax', False)
            sum_amount_total += line_sale_order.get('amount_total', False)
        row += 1
        worksheet.write(row, 2, "Tổng", footer_bold_color)
        worksheet.write(row, 3, sum_amount_untaxed, footer_bold_color)
        # worksheet3.write(row, 4, sum_amount_discount, header_bold_color)
        worksheet.write(row, 4, sum_amount_tax, footer_bold_color)
        worksheet.write(row, 5, sum_amount_total, footer_bold_color)

    def create_worksheet4(self, workbook, worksheet):
        merge_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': '16', 'border': 1})
        header1_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0'})
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', 'bg_color': 'cce0ff'})
        footer_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', })
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '12', 'align': 'left', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', })
        back_color = 'A2:I2'
        back_color_date = 'A3:I3'

        worksheet.set_row(1, 25)
        worksheet.set_row(2, 18)
        worksheet.merge_range(back_color, unicode("SỔ TRẢ HÀNG MUA", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 60)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        # worksheet3.set_column('G:G', 20)

        row = 4
        summary_header = ['Ngày đặt hàng', 'Số đơn hàng', 'Tên khách hàng', 'Tổng chưa thuế', 'Thuế', 'Tổng tiền']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        sale_order_data = self.get_purchase_order_data(('purchase_order_return', '=', True))
        sum_amount_untaxed = 0.0
        sum_amount_discount = 0.0
        sum_amount_tax = 0.0
        sum_amount_total = 0.0
        for line_sale_order in sale_order_data:
            row += 1
            worksheet.write(row, 0, line_sale_order.get('date_order', False), body_bold_color)
            worksheet.write(row, 1, line_sale_order.get('order_name', False), body_bold_color)
            worksheet.write(row, 2, line_sale_order.get('partner_name', False), body_bold_color)
            worksheet.write(row, 3, line_sale_order.get('amount_untaxed', False), body_bold_color)
            # worksheet3.write(row, 4, line_sale_order.get('amount_discount', False), body_bold_color)
            worksheet.write(row, 4, line_sale_order.get('amount_tax', False), body_bold_color)
            worksheet.write(row, 5, line_sale_order.get('amount_total', False), body_bold_color)
            sum_amount_untaxed += line_sale_order.get('amount_untaxed', False)
            sum_amount_discount += line_sale_order.get('amount_discount', False)
            sum_amount_tax += line_sale_order.get('amount_tax', False)
            sum_amount_total += line_sale_order.get('amount_total', False)
        row += 1
        worksheet.write(row, 2, "Tổng", footer_bold_color)
        worksheet.write(row, 3, sum_amount_untaxed, footer_bold_color)
        # worksheet3.write(row, 4, sum_amount_discount, header_bold_color)
        worksheet.write(row, 4, sum_amount_tax, footer_bold_color)
        worksheet.write(row, 5, sum_amount_total, footer_bold_color)

    def create_worksheet5(self, workbook, worksheet):
        merge_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': '16', 'border': 1})
        header1_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0'})
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', 'bg_color': 'cce0ff'})
        footer_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', })
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '12', 'align': 'left', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', })
        back_color = 'A2:I2'
        back_color_date = 'A3:I3'

        worksheet.set_row(1, 25)
        worksheet.set_row(2, 18)
        worksheet.merge_range(back_color, unicode("PHIẾU THU", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 60)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        # worksheet3.set_column('G:G', 20)

        row = 4
        summary_header = ['Ngày lập phiếu', 'Số Phiếu Thu', 'Tên khách hàng', 'Tổng tiền']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        sale_order_data = self.get_account_voucher_data(('voucher_type', '=', 'sale'))
        sum_amount_total = 0.0
        for line_sale_order in sale_order_data:
            row += 1
            worksheet.write(row, 0, line_sale_order.get('date_order', False), body_bold_color)
            worksheet.write(row, 1, line_sale_order.get('voucher_number', False), body_bold_color)
            worksheet.write(row, 2, line_sale_order.get('partner_name', False), body_bold_color)
            worksheet.write(row, 3, line_sale_order.get('amount', False), body_bold_color)
            sum_amount_total += line_sale_order.get('amount', False)
        row += 1
        worksheet.write(row, 2, "Tổng", footer_bold_color)
        worksheet.write(row, 3, sum_amount_total, footer_bold_color)

    def create_worksheet6(self, workbook, worksheet):
        merge_format = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': '16', 'border': 1})
        header1_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0'})
        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', 'bg_color': 'cce0ff'})
        footer_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', })
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '12', 'align': 'left', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', })
        back_color = 'A2:I2'
        back_color_date = 'A3:I3'

        worksheet.set_row(1, 25)
        worksheet.set_row(2, 18)
        worksheet.merge_range(back_color, unicode("PHIẾU THU", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 60)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        # worksheet3.set_column('G:G', 20)

        row = 4
        summary_header = ['Ngày lập phiếu', 'Số Phiếu Thu', 'Tên khách hàng', 'Tổng tiền']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        sale_order_data = self.get_account_voucher_data(('voucher_type', '=', 'purchase'))
        sum_amount_total = 0.0
        for line_sale_order in sale_order_data:
            row += 1
            worksheet.write(row, 0, line_sale_order.get('date_order', False), body_bold_color)
            worksheet.write(row, 1, line_sale_order.get('voucher_number', False), body_bold_color)
            worksheet.write(row, 2, line_sale_order.get('partner_name', False), body_bold_color)
            worksheet.write(row, 3, line_sale_order.get('amount_untaxed', False), body_bold_color)
            sum_amount_total += line_sale_order.get('amount_total', False)
        row += 1
        worksheet.write(row, 2, "Tổng", footer_bold_color)
        worksheet.write(row, 3, sum_amount_total, footer_bold_color)