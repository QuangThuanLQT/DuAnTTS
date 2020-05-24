# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
# import cStringIO
import base64
from io import StringIO
import xlsxwriter
from datetime import datetime


class sale_order_line_report(models.TransientModel):
    _name = 'so.ban.hang'

    partner_id = fields.Many2one('res.partner', String="Customer")
    product_id = fields.Many2one('product.product', String="Product")
    start_date = fields.Date(String='Start Date', required=True)
    end_date = fields.Date(String='End Date')

    def get_don_ban_hang(self, conditions_add=False):
        conditions = [('order_id.state', '=', 'sale')]
        if self.start_date:
            conditions.append(('date_order', '>=', self.start_date))
        if self.end_date:
            conditions.append(('date_order', '<=', self.end_date))
        if self.partner_id:
            conditions.append(('order_partner_id', '=', self.partner_id.id))
        if self.product_id:
            conditions.append(('product_id', '=', self.product_id.id))

        if conditions_add:
            conditions.append(conditions_add)
        order_line_ids = self.env['sale.order.line'].search(conditions, order='date_order asc')

        line_data = []
        for order_line in order_line_ids:
            line_data.append({
                'date_order': datetime.strptime(order_line.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                    "%d/%m/%Y"),
                'order_name': order_line.order_id.name,
                'partner_name': order_line.order_partner_id.name,
                'default_code': order_line.product_id.default_code,
                'product_name': order_line.product_id.name,
                'uom': order_line.product_uom.name,
                'qty': order_line.product_uom_qty if conditions_add else -order_line.product_uom_qty if order_line.sale_order_return else order_line.product_uom_qty,
                'price_unit': order_line.final_price if conditions_add else -order_line.final_price if order_line.sale_order_return else order_line.final_price,
                'doanh_so': order_line.final_price * order_line.product_uom_qty if conditions_add else -(
                            order_line.final_price * order_line.product_uom_qty)
                if order_line.sale_order_return else order_line.final_price * order_line.product_uom_qty,
                'discount': order_line.discount,
            })

        return line_data

    def get_don_mua_hang(self, conditions_add=False):
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

    def get_sale_report_group_partner(self, fields_data=False, group_by=False):
        conditions = [('state', 'not in', ('draft', 'cancel', 'sent'))]
        if self.start_date:
            conditions.append(('date', '>=', self.start_date))
        if self.end_date:
            conditions.append(('date', '<=', self.end_date))
        if self.partner_id:
            conditions.append(('partner_id', '=', self.partner_id.id))
        r = []
        group_by_ids = self.env['sale.report'].read_group(conditions, fields=fields_data, groupby=group_by)
        for group in group_by_ids:
            r.append({
                group_by: group[group_by],
                'price_subtotal': group['price_subtotal']
            })
        return r

    @api.model
    def get_data_report(self):
        self.ensure_one()
        data_report = {}

        data_report.update({
            'don_ban_hang': self.get_don_ban_hang(('sale_order_return', '=', False)),
            'don_tra_ban_hang': self.get_don_ban_hang(('sale_order_return', '=', True)),
            'don_ban_hang_th': self.get_don_ban_hang(),
            'don_mua_hang': self.get_don_mua_hang(('sale_order_return', '=', False)),
            'don_tra_mua_hang': self.get_don_mua_hang(('sale_order_return', '=', True)),
            'don_mua_hang_th': self.get_don_mua_hang(),
        })
        return data_report

    @api.multi
    def print_excel(self):
        output = StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        bold = workbook.add_format({'bold': True})
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
        data_report = self.get_data_report()

        # TODO CHI TIET BAN HANG ---------------------------------------------------------------------------------------------------------------------------------
        # TODO CHI TIET BAN HANG SHEET
        worksheet3 = workbook.add_worksheet('So ban hang')
        worksheet = workbook.add_worksheet('So chi tiet ban hang')
        worksheet4 = workbook.add_worksheet('So tra hang ban')
        worksheet1 = workbook.add_worksheet('So chi tiet tra hang ban')
        worksheet5 = workbook.add_worksheet('So ban hang tong hop')
        worksheet2 = workbook.add_worksheet('So chi tiet ban hang tong hop')
        worksheet6 = workbook.add_worksheet('Nhom theo thuong hieu')
        worksheet7 = workbook.add_worksheet('Nhom theo san pham')
        worksheet8 = workbook.add_worksheet('Nhom theo nhom san pham')
        worksheet9 = workbook.add_worksheet('Nhom theo khach hang')
        worksheet.set_row(1, 25)
        worksheet.set_row(2, 18)
        worksheet.merge_range(back_color, unicode("SỔ CHI TIẾT BÁN HÀNG", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 60)
        worksheet.set_column('D:D', 30)
        worksheet.set_column('E:E', 65)
        worksheet.set_column('F:F', 10)
        worksheet.set_column('G:G', 22)
        worksheet.set_column('H:H', 15)
        worksheet.set_column('I:I', 20)
        # worksheet.set_column('J:J', 15)

        row = 4
        summary_header = ['Ngày đặt hàng', 'Số đơn hàng', 'Tên khách hàng', 'Mã nội bộ', 'Tên hàng', 'ĐVT',
                          'Tổng số lượng bán', 'Đơn giá', 'Doanh số bán']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        sale_order_data = data_report.get('don_ban_hang', False)
        sum_doanh_so = 0.0
        for line_sale_order in sale_order_data:
            row += 1
            worksheet.write(row, 0, line_sale_order.get('date_order', False), body_bold_color)
            worksheet.write(row, 1, line_sale_order.get('order_name', False), body_bold_color)
            worksheet.write(row, 2, line_sale_order.get('partner_name', False), body_bold_color)
            worksheet.write(row, 3, line_sale_order.get('default_code', False), body_bold_color)
            worksheet.write(row, 4, line_sale_order.get('product_name', False), body_bold_color)
            worksheet.write(row, 5, line_sale_order.get('uom', False), body_bold_color)
            worksheet.write(row, 6, line_sale_order.get('qty', False), body_bold_color)
            worksheet.write(row, 7, line_sale_order.get('price_unit', False), body_bold_color)
            worksheet.write(row, 8, line_sale_order.get('doanh_so', False), body_bold_color)
            # worksheet.write(row, 9, line_sale_order.get('discount', False), body_bold_color)
            sum_doanh_so += line_sale_order.get('doanh_so', False)
        row += 1
        worksheet.write(row, 7, "Tổng doanh số", footer_bold_color)
        worksheet.write(row, 8, sum_doanh_so, footer_bold_color)

        # TODO CHI TIET TRA HANG BAN SHEET

        worksheet1.set_row(1, 25)
        worksheet1.set_row(2, 18)
        worksheet1.merge_range(back_color, unicode("SỔ CHI TIẾT TRẢ HÀNG BÁN", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet1.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet1.set_column('A:A', 20)
        worksheet1.set_column('B:B', 20)
        worksheet1.set_column('C:C', 60)
        worksheet1.set_column('D:D', 30)
        worksheet1.set_column('E:E', 65)
        worksheet1.set_column('F:F', 10)
        worksheet1.set_column('G:G', 22)
        worksheet1.set_column('H:H', 15)
        worksheet1.set_column('I:I', 20)
        # worksheet1.set_column('J:J', 15)

        row = 4
        summary_header = ['Ngày lập đơn', 'Số đơn hàng', 'Tên khách hàng', 'Mã nội bộ', 'Tên hàng', 'ĐVT',
                          'Tổng số lượng trả', 'Đơn giá', 'Tổng tiền']
        [worksheet1.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        sale_order_data = data_report.get('don_tra_ban_hang', False)
        sum_doanh_so = 0.0
        for line_sale_order in sale_order_data:
            row += 1
            worksheet1.write(row, 0, line_sale_order.get('date_order', False), body_bold_color)
            worksheet1.write(row, 1, line_sale_order.get('order_name', False), body_bold_color)
            worksheet1.write(row, 2, line_sale_order.get('partner_name', False), body_bold_color)
            worksheet1.write(row, 3, line_sale_order.get('default_code', False), body_bold_color)
            worksheet1.write(row, 4, line_sale_order.get('product_name', False), body_bold_color)
            worksheet1.write(row, 5, line_sale_order.get('uom', False), body_bold_color)
            worksheet1.write(row, 6, line_sale_order.get('qty', False), body_bold_color)
            worksheet1.write(row, 7, line_sale_order.get('price_unit', False), body_bold_color)
            worksheet1.write(row, 8, line_sale_order.get('doanh_so', False), body_bold_color)
            # worksheet1.write(row, 9, line_sale_order.get('discount', False), body_bold_color)
            sum_doanh_so += line_sale_order.get('doanh_so', False)
        row += 1
        worksheet1.write(row, 7, "Tổng doanh số", footer_bold_color)
        worksheet1.write(row, 8, sum_doanh_so, footer_bold_color)

        # TODO CHI TIET BAN HANG TONG HOP SHEET

        worksheet2.set_row(1, 25)
        worksheet2.set_row(2, 18)
        worksheet2.merge_range(back_color, unicode("SỔ CHI TIẾT BÁN HÀNG TỔNG HỢP", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet2.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet2.set_column('A:A', 20)
        worksheet2.set_column('B:B', 20)
        worksheet2.set_column('C:C', 60)
        worksheet2.set_column('D:D', 30)
        worksheet2.set_column('E:E', 65)
        worksheet2.set_column('F:F', 10)
        worksheet2.set_column('G:G', 22)
        worksheet2.set_column('H:H', 15)
        worksheet2.set_column('I:I', 20)
        # worksheet2.set_column('J:J', 15)

        row = 4
        summary_header = ['Ngày lập đơn', 'Số đơn hàng', 'Tên khách hàng', 'Mã nội bộ', 'Tên hàng', 'ĐVT',
                          'Tổng số lượng', 'Đơn giá', 'Tổng tiền']
        [worksheet2.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        sale_order_data = data_report.get('don_ban_hang_th', False)
        sum_doanh_so = 0.0
        for line_sale_order in sale_order_data:
            row += 1
            worksheet2.write(row, 0, line_sale_order.get('date_order', False), body_bold_color)
            worksheet2.write(row, 1, line_sale_order.get('order_name', False), body_bold_color)
            worksheet2.write(row, 2, line_sale_order.get('partner_name', False), body_bold_color)
            worksheet2.write(row, 3, line_sale_order.get('default_code', False), body_bold_color)
            worksheet2.write(row, 4, line_sale_order.get('product_name', False), body_bold_color)
            worksheet2.write(row, 5, line_sale_order.get('uom', False), body_bold_color)
            worksheet2.write(row, 6, line_sale_order.get('qty', False), body_bold_color)
            worksheet2.write(row, 7, line_sale_order.get('price_unit', False), body_bold_color)
            worksheet2.write(row, 8, line_sale_order.get('doanh_so', False), body_bold_color)
            # worksheet2.write(row, 9, line_sale_order.get('discount', False), body_bold_color)
            sum_doanh_so += line_sale_order.get('doanh_so', False)
        row += 1
        worksheet2.write(row, 7, "Tổng doanh số", footer_bold_color)
        worksheet2.write(row, 8, sum_doanh_so, footer_bold_color)

        back_color = 'A2:F2'
        back_color_date = 'A3:F3'
        # TODO BAN HANG ---------------------------------------------------------------------------------------------------------------------------------
        # TODO BAN HANG SHEET

        worksheet3.set_row(1, 25)
        worksheet3.set_row(2, 18)
        worksheet3.merge_range(back_color, unicode("SỔ BÁN HÀNG", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet3.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet3.set_column('A:A', 20)
        worksheet3.set_column('B:B', 20)
        worksheet3.set_column('C:C', 60)
        worksheet3.set_column('D:D', 20)
        worksheet3.set_column('E:E', 20)
        worksheet3.set_column('F:F', 20)
        # worksheet3.set_column('G:G', 20)

        row = 4
        summary_header = ['Ngày đặt hàng', 'Số đơn hàng', 'Tên khách hàng', 'Tổng chưa thuế', 'Thuế', 'Tổng tiền']
        [worksheet3.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        sale_order_data = data_report.get('don_mua_hang', False)
        sum_amount_untaxed = 0.0
        sum_amount_discount = 0.0
        sum_amount_tax = 0.0
        sum_amount_total = 0.0
        for line_sale_order in sale_order_data:
            row += 1
            worksheet3.write(row, 0, line_sale_order.get('date_order', False), body_bold_color)
            worksheet3.write(row, 1, line_sale_order.get('order_name', False), body_bold_color)
            worksheet3.write(row, 2, line_sale_order.get('partner_name', False), body_bold_color)
            worksheet3.write(row, 3, line_sale_order.get('amount_untaxed', False), body_bold_color)
            # worksheet3.write(row, 4, line_sale_order.get('amount_discount', False), body_bold_color)
            worksheet3.write(row, 4, line_sale_order.get('amount_tax', False), body_bold_color)
            worksheet3.write(row, 5, line_sale_order.get('amount_total', False), body_bold_color)
            sum_amount_untaxed += line_sale_order.get('amount_untaxed', False)
            sum_amount_discount += line_sale_order.get('amount_discount', False)
            sum_amount_tax += line_sale_order.get('amount_tax', False)
            sum_amount_total += line_sale_order.get('amount_total', False)
        row += 1
        worksheet3.write(row, 2, "Tổng", footer_bold_color)
        worksheet3.write(row, 3, sum_amount_untaxed, footer_bold_color)
        # worksheet3.write(row, 4, sum_amount_discount, header_bold_color)
        worksheet3.write(row, 4, sum_amount_tax, footer_bold_color)
        worksheet3.write(row, 5, sum_amount_total, footer_bold_color)

        # TODO TRA HANG BAN SHEET

        worksheet4.set_row(1, 25)
        worksheet4.set_row(2, 18)
        worksheet4.merge_range(back_color, unicode("SỔ TRẢ HÀNG BÁN", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet4.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet4.set_column('A:A', 20)
        worksheet4.set_column('B:B', 20)
        worksheet4.set_column('C:C', 60)
        worksheet4.set_column('D:D', 20)
        worksheet4.set_column('E:E', 20)
        worksheet4.set_column('F:F', 20)
        # worksheet4.set_column('G:G', 20)

        row = 4
        summary_header = ['Ngày lập đơn', 'Số đơn hàng', 'Tên khách hàng', 'Tổng chưa thuế', 'Thuế', 'Tổng tiền']
        [worksheet4.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        sale_order_data = data_report.get('don_tra_mua_hang', False)
        sum_amount_untaxed = 0.0
        sum_amount_discount = 0.0
        sum_amount_tax = 0.0
        sum_amount_total = 0.0
        for line_sale_order in sale_order_data:
            row += 1
            worksheet4.write(row, 0, line_sale_order.get('date_order', False), body_bold_color)
            worksheet4.write(row, 1, line_sale_order.get('order_name', False), body_bold_color)
            worksheet4.write(row, 2, line_sale_order.get('partner_name', False), body_bold_color)
            worksheet4.write(row, 3, line_sale_order.get('amount_untaxed', False), body_bold_color)
            # worksheet4.write(row, 4, line_sale_order.get('amount_discount', False), body_bold_color)
            worksheet4.write(row, 4, line_sale_order.get('amount_tax', False), body_bold_color)
            worksheet4.write(row, 5, line_sale_order.get('amount_total', False), body_bold_color)
            sum_amount_untaxed += line_sale_order.get('amount_untaxed', False)
            sum_amount_discount += line_sale_order.get('amount_discount', False)
            sum_amount_tax += line_sale_order.get('amount_tax', False)
            sum_amount_total += line_sale_order.get('amount_total', False)

        row += 1
        worksheet4.write(row, 2, "Tổng", footer_bold_color)
        worksheet4.write(row, 3, sum_amount_untaxed, footer_bold_color)
        # worksheet4.write(row, 4, sum_amount_discount, header_bold_color)
        worksheet4.write(row, 4, sum_amount_tax, footer_bold_color)
        worksheet4.write(row, 5, sum_amount_total, footer_bold_color)

        # TODO BAN HANG TONG HOP SHEET
        worksheet5.set_row(1, 25)
        worksheet5.set_row(2, 18)
        worksheet5.merge_range(back_color, unicode("SỔ BÁN HÀNG TỔNG HỢP", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet5.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet5.set_column('A:A', 20)
        worksheet5.set_column('B:B', 20)
        worksheet5.set_column('C:C', 60)
        worksheet5.set_column('D:D', 20)
        worksheet5.set_column('E:E', 20)
        worksheet5.set_column('F:F', 20)
        # worksheet5.set_column('G:G', 20)

        row = 4
        summary_header = ['Ngày lập đơn', 'Số đơn hàng', 'Tên khách hàng', 'Tổng chưa thuế', 'Thuế', 'Tổng tiền']
        [worksheet5.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        sale_order_data = data_report.get('don_mua_hang_th', False)
        sum_amount_untaxed = 0.0
        sum_amount_discount = 0.0
        sum_amount_tax = 0.0
        sum_amount_total = 0.0
        for line_sale_order in sale_order_data:
            row += 1
            worksheet5.write(row, 0, line_sale_order.get('date_order', False), body_bold_color)
            worksheet5.write(row, 1, line_sale_order.get('order_name', False), body_bold_color)
            worksheet5.write(row, 2, line_sale_order.get('partner_name', False), body_bold_color)
            worksheet5.write(row, 3, line_sale_order.get('amount_untaxed', False), body_bold_color)
            # worksheet5.write(row, 4, line_sale_order.get('amount_discount', False), body_bold_color)
            worksheet5.write(row, 4, line_sale_order.get('amount_tax', False), body_bold_color)
            worksheet5.write(row, 5, line_sale_order.get('amount_total', False), body_bold_color)
            sum_amount_untaxed += line_sale_order.get('amount_untaxed', False)
            sum_amount_discount += line_sale_order.get('amount_discount', False)
            sum_amount_tax += line_sale_order.get('amount_tax', False)
            sum_amount_total += line_sale_order.get('amount_total', False)

        row += 1
        worksheet5.write(row, 2, "Tổng", footer_bold_color)
        worksheet5.write(row, 3, sum_amount_untaxed, footer_bold_color)
        # worksheet5.write(row, 4, sum_amount_discount, header_bold_color)
        worksheet5.write(row, 4, sum_amount_tax, footer_bold_color)
        worksheet5.write(row, 5, sum_amount_total, footer_bold_color)

        # TODO SALE REPORT ------------------------------------
        back_color = 'A2:B2'
        back_color_date = 'A3:B3'

        # TODO NHOM THEO THUONG HIEU

        worksheet6.set_row(1, 25)
        worksheet6.set_row(2, 18)
        worksheet6.merge_range(back_color, unicode("NHÓM THEO THƯƠNG HIỆU", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet6.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet6.set_column('A:A', 70)
        worksheet6.set_column('B:B', 20)

        row = 4
        summary_header = ['Thương Hiệu', 'Tổng Chưa Thuế']
        [worksheet6.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        group_partner_list = self.get_sale_report_group_partner(['brand_name', 'price_subtotal'], 'brand_name')
        group_partner_list.sort(key=lambda k: k['price_subtotal'], reverse=True)
        hight_body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '12', 'align': 'left', 'valign': 'vcenter', 'border': 1,
             'num_format': '#,##0', 'bg_color': '99CC00'})

        count_top = 0
        price_total = 0.0
        for brand_line in group_partner_list:
            row += 1
            if count_top < 20:
                worksheet6.write(row, 0, brand_line['brand_name'], hight_body_bold_color)
                worksheet6.write(row, 1, brand_line['price_subtotal'], hight_body_bold_color)
                count_top += 1
            else:
                worksheet6.write(row, 0, brand_line['brand_name'], body_bold_color)
                worksheet6.write(row, 1, brand_line['price_subtotal'], body_bold_color)
            price_total += brand_line['price_subtotal']
        row += 1
        worksheet6.write(row, 0, 'Tổng', footer_bold_color)
        worksheet6.write(row, 1, price_total, footer_bold_color)

        # TODO NHOM THEO SAN PHAM

        worksheet7.set_row(1, 25)
        worksheet7.set_row(2, 18)
        worksheet7.merge_range(back_color, unicode("NHÓM THEO SẢN PHẨM", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet7.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet7.set_column('A:A', 70)
        worksheet7.set_column('B:B', 20)

        row = 4
        summary_header = ['Sản Phẩm', 'Tổng Chưa Thuế']
        [worksheet7.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color)
         for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        group_partner_list = self.get_sale_report_group_partner(['product_id', 'price_subtotal'], 'product_id')
        group_partner_list.sort(key=lambda k: k['price_subtotal'], reverse=True)

        count_top = 0
        price_total = 0.0
        for product_line in group_partner_list:
            row += 1
            if count_top < 100:
                worksheet7.write(row, 0, product_line['product_id'][1], hight_body_bold_color)
                worksheet7.write(row, 1, product_line['price_subtotal'], hight_body_bold_color)
                count_top += 1
            else:
                worksheet7.write(row, 0, product_line['product_id'][1], body_bold_color)
                worksheet7.write(row, 1, product_line['price_subtotal'], body_bold_color)
            price_total += product_line['price_subtotal']
        row += 1
        worksheet7.write(row, 0, 'Tổng', footer_bold_color)
        worksheet7.write(row, 1, price_total, footer_bold_color)

        # TODO NHOM THEO NHOM SAN PHAM

        worksheet8.set_row(1, 25)
        worksheet8.set_row(2, 18)
        worksheet8.merge_range(back_color, unicode("NHÓM THEO NHÓM SẢN PHẨM", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet8.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet8.set_column('A:A', 70)
        worksheet8.set_column('B:B', 20)

        row = 4
        summary_header = ['Nhóm Sản Phẩm', 'Tổng Chưa Thuế']
        [worksheet8.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"),
                          header_bold_color)
         for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        group_partner_list = self.get_sale_report_group_partner(['group_id', 'price_subtotal'],
                                                                'group_id')
        group_partner_list.sort(key=lambda k: k['price_subtotal'], reverse=True)

        count_top = 0
        group_unknow = 0
        price_total = 0.0
        for group_line in group_partner_list:
            if group_line['group_id']:
                row += 1
                if count_top < 10:
                    worksheet8.write(row, 0, group_line['group_id'][1], hight_body_bold_color)
                    worksheet8.write(row, 1, group_line['price_subtotal'], hight_body_bold_color)
                    count_top += 1
                else:
                    worksheet8.write(row, 0, group_line['group_id'][1], body_bold_color)
                    worksheet8.write(row, 1, group_line['price_subtotal'], body_bold_color)
            else:
                group_unknow = group_line['price_subtotal']
            price_total += group_line['price_subtotal']
        if group_unknow:
            row += 1
            if count_top < 10:
                worksheet8.write(row, 0, 'Không xác định', hight_body_bold_color)
                worksheet8.write(row, 1, group_unknow, hight_body_bold_color)
                count_top += 1
            else:
                worksheet8.write(row, 0, 'Không xác định', body_bold_color)
                worksheet8.write(row, 1, group_unknow, body_bold_color)
        row += 1
        worksheet8.write(row, 0, 'Tổng', footer_bold_color)
        worksheet8.write(row, 1, price_total, footer_bold_color)

        # TODO NHOM THEO NHOM KHACH HANG

        worksheet9.set_row(1, 25)
        worksheet9.set_row(2, 18)
        worksheet9.merge_range(back_color, unicode("NHÓM THEO KHÁCH HÀNG", "utf-8"), merge_format)
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT).strftime(
            "%d/%m/%Y") if self.end_date else datetime.today().strftime("%d/%m/%Y")
        string = "Từ ngày %s đến ngày %s" % (start_date, end_date)
        worksheet9.merge_range(back_color_date, unicode(string, "utf-8"), header1_bold_color)

        worksheet9.set_column('A:A', 70)
        worksheet9.set_column('B:B', 20)

        row = 4
        summary_header = ['Khách Hàng', 'Tổng Chưa Thuế']
        [worksheet9.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"),
                          header_bold_color)
         for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]

        group_partner_list = self.get_sale_report_group_partner(['partner_id', 'price_subtotal'],
                                                                'partner_id')
        group_partner_list.sort(key=lambda k: k['price_subtotal'], reverse=True)

        count_top = 0
        price_total = 0.0
        for partner_line in group_partner_list:
            row += 1
            if count_top < 10:
                worksheet9.write(row, 0, partner_line['partner_id'][1], hight_body_bold_color)
                worksheet9.write(row, 1, partner_line['price_subtotal'], hight_body_bold_color)
                count_top += 1
            else:
                worksheet9.write(row, 0, partner_line['partner_id'][1], body_bold_color)
                worksheet9.write(row, 1, partner_line['price_subtotal'], body_bold_color)
            price_total += partner_line['price_subtotal']
        row += 1
        worksheet9.write(row, 0, 'Tổng', footer_bold_color)
        worksheet9.write(row, 1, price_total, footer_bold_color)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'SO_CHI_TIET_BAN_HANG.xlsx', 'datas_fname': 'SO_CHI_TIET_BAN_HANG.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}
