# -*- coding: utf-8 -*-
import StringIO

import StringIO

import xlsxwriter
from odoo import models, fields, api, exceptions
from datetime import datetime
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class vieterp_sale_return(models.Model):
    _inherit = 'sale.order'

    sale_order_return = fields.Boolean(default=False)
    validate_by = fields.Many2one('res.users', string="Validate By")
    sale_order = fields.Many2one('sale.order', domain=[('sale_order_return', '=', False)])
    receive_method = fields.Selection([('allow', 'Nhận hàng trả lại tại kho'), ('stop', 'Nhận hàng trả lại tại địa chỉ giao hàng')],string="Phương thức nhận hàng")
    location_return = fields.Selection([('allow', 'Kho Bình thường'), ('stop', 'Kho hư hỏng')],string="Kho lưu trữ sản phẩm")
    sale_return_state = fields.Selection([('draft', 'Draft'), ('sale_order', 'Order Return'), ('cancel', 'Cancel')],
                                         compute='get_sale_return_state')


    @api.multi
    def get_sale_return_state(self):
        for rec in self:
            if rec.state in ('draft', 'sent', 'waiting'):
                rec.sale_return_state = 'draft'
            elif rec.state in ('sale', 'done'):
                rec.sale_return_state = 'sale_order'
            else:
                rec.sale_return_state = 'cancel'

    @api.multi
    def action_draft_return(self):
        self.state = 'draft'

    @api.multi
    def action_confirm_return(self):
        self.state = 'sale_order'

    @api.multi
    def action_cancel(self):
        self.state = 'cancel'

    @api.onchange('sale_order')
    def onchange_sale_order(self):
        if self.sale_order:
            self.order_line = False
            for line in self.sale_order.order_line:
                data_order = line.copy_data({})[0]
                self.order_line += self.order_line.new(data_order)

    def _get_datetime_utc(self, datetime_val):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(datetime_val, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime('%d/%m/%Y %H:%M:%S')
        return resuft

    @api.model
    def print_sale_return_excel(self, response, type=None):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        sale_return_ids = self.env['sale.order'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Sale Return')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:A', 8)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:R', 16)
        summary_header = ['Reference Return', 'Create Date', 'Customer', 'Salesperson',
                          'Sale Order', 'Total', 'Status','Created by','Validate by']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for sale_return_id in sale_return_ids:
            row += 1
            state = dict(self.env['sale.order'].fields_get(allfields=['sale_return_state'])['sale_return_state'][
                             'selection'])

            worksheet.write(row, 0, sale_return_id.name or '')
            worksheet.write(row, 1, self._get_datetime_utc(sale_return_id.date_order))
            worksheet.write(row, 2, sale_return_id.partner_id.display_name or '', text_style)
            worksheet.write(row, 3, sale_return_id.user_id.name or '')
            worksheet.write(row, 4, sale_return_id.sale_order.name or '')
            worksheet.write(row, 5, sale_return_id.amount_total or 0)
            worksheet.write(row, 6, state.get(sale_return_id.sale_return_state) or '')
            worksheet.write(row, 7, sale_return_id.create_uid.name or '')
            worksheet.write(row, 8, sale_return_id.validate_by.name or '')
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.model
    def print_sale_return_detail_excel(self, response, type=None):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        sale_return_ids = self.env['sale.order'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Sale Return Detail')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:A', 8)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:R', 16)
        summary_header = ['Reference Return', 'Create Date', 'Customer Code','Customers','Phone Customers','Salespersons','Sale Order','Total', 'Product Variant Name',
                          'Quantity', 'Unit Price', 'Subtotal', 'Status','Created by','Validate by']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for sale_return_id in sale_return_ids:
            for line in sale_return_id.order_line:
                row += 1
                state = dict(self.env['sale.order'].fields_get(allfields=['sale_return_state'])['sale_return_state'][
                                 'selection'])

                worksheet.write(row, 0, sale_return_id.name or '')
                worksheet.write(row, 1, self._get_datetime_utc(sale_return_id.date_order))
                worksheet.write(row, 2, sale_return_id.partner_id.ref or '', body_bold_color_number)
                worksheet.write(row, 3, sale_return_id.partner_id.display_name or '')
                worksheet.write(row, 4, sale_return_id.partner_id.phone or '')
                worksheet.write(row, 5, sale_return_id.user_id.name or '')
                worksheet.write(row, 6, sale_return_id.sale_order.name or '')
                worksheet.write(row, 7, sale_return_id.amount_total or 0)
                worksheet.write(row, 8, line.product_id.name or '')
                worksheet.write(row, 9, line.product_uom_qty or 0)
                worksheet.write(row, 10, line.price_unit or 0)
                worksheet.write(row, 11, line.price_subtotal or 0)
                worksheet.write(row, 12, state.get(sale_return_id.sale_return_state) or '')
                worksheet.write(row, 13, sale_return_id.create_uid.name or '')
                worksheet.write(row, 14, sale_return_id.validate_by.name or '')
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    sale_order_return = fields.Boolean(related="order_id.sale_order_return")