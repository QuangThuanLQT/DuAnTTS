# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import StringIO
import xlsxwriter
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class res_partner_inherit(models.Model):
    _inherit = 'res.partner'

    product_puchase_count = fields.Integer(compute='_product_puchase_count')

    def _product_puchase_count(self):
        for rec in self:
            product_data = self.env['sale.order.line'].search([('order_partner_id', '=', rec.id), ('order_id.state', '=', 'sale'), ('order_id.sale_order_return', '=', False)])
            rec.product_puchase_count = len(product_data.mapped('product_id'))

    def res_product_purchase(self):
        for rec in self:
            so_line_ids = self.env['sale.order.line'].search([('order_partner_id', '=', rec.id), ('order_id.state', '=', 'sale'), ('order_id.sale_order_return', '=', False)])
            product_list = so_line_ids.mapped('product_id').ids
            for product in product_list:
                product_qty = sum(self.env['sale.order.line'].search([('id', 'in', so_line_ids.ids), ('product_id', '=', product)]).mapped('product_uom_qty'))
                time_purchase = self.env['sale.order'].search([('partner_id', '=', rec.id), ('state', '=', 'sale'),('sale_order_return', '=', False),
                    ('order_line.product_id', '=', product)], order='confirmation_date DESC', limit=1).mapped('confirmation_date')
                value = self.env['product.purchase'].search([('partner_id', '=', rec.id), ('product_id', '=', product)])
                if not value and product_qty:
                    value = self.env['product.purchase'].create({
                        'partner_id': rec.id,
                        'product_id': product,
                        'product_qty' : product_qty,
                        'time_partner_purchase' : time_purchase,
                    })
                elif value and not product_qty:
                    value.unlink()
                elif value and product_qty:
                    value.write({
                        'product_qty' : product_qty,
                        'time_partner_purchase': time_purchase,
                    })
                    pass
            action = self.env.ref('prinizi_sale_customer_product_purchase.res_product_purchase_action').read()[0]
            action['domain'] = [('product_id', 'in', product_list), ('partner_id', '=', rec.id)]
            return action


class product_puchase(models.Model):
    _name = 'product.purchase'
    _order = 'amount_partner_purchase desc'

    partner_id = fields.Many2one('res.partner')
    product_id = fields.Many2one('product.product', string='Product Name')
    product_puchase_id = fields.Char(compute='get_product_id', store=True)
    name_atr = fields.Char(compute='get_name')
    product_qty = fields.Integer()
    time_partner_purchase = fields.Datetime()
    amount_partner_purchase = fields.Float(digits=(16,0), compute='_product_puchase', store=True)
    trang_thai_hd = fields.Selection([
        ('active', 'Đang kinh doanh'),
        ('unactive', 'Ngừng kinh doanh')
    ], compute='get_trang_thai_hd', string='Trạng thái', store=True)

    @api.depends('product_id','product_id.active')
    def get_trang_thai_hd(self):
        for rec in self:
            if rec.product_id.active:
                rec.trang_thai_hd = 'active'
            else:
                rec.trang_thai_hd = 'unactive'

    @api.multi
    def get_name(self):
        for record in self:
            variable_attributes = record.product_id.attribute_line_ids.filtered(lambda l: len(l.value_ids) >= 1).mapped('attribute_id')
            variant = record.product_id.attribute_value_ids._variant_name(variable_attributes)
            record.name_atr = variant and "%s - %s" % (record.product_id.name, variant) or record.product_id.name

    def _get_datetime_utc(self, datetime_val):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(datetime_val, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime('%d/%m/%Y %H:%M:%S')
        return resuft

    @api.depends('product_id')
    def get_product_id(self):
        for record in self:
            record.product_puchase_id = record.product_id.code

    @api.depends('product_qty', 'product_id.lst_price')
    def _product_puchase(self):
        for record in self:
            record.amount_partner_purchase = record.product_qty * record.product_id.lst_price

    @api.model
    def get_product_purchase_search(self, product_name):
        if product_name:
            product_id = self.search([('product_puchase_id', '=like','%' + product_name + '%')])
            return product_id.ids

    @api.model
    def export_overview_product_purchase(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        product_purchase_ids = self.env['product.purchase'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Overview')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')
        header_bold_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'center', 'valign': 'vcenter'})
        header_bold_number.set_num_format('#,##0')

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 10)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 16)
        worksheet.set_column('E:E', 16)
        worksheet.set_column('F:F', 11)

        summary_header = ['STT', 'Reference', 'Product name', 'Time', 'Quantity Purchased', 'Amount']

        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
        stt = 1

        for rec in product_purchase_ids:
            row += 1
            date = ''
            if rec.time_partner_purchase:
                date = self._get_datetime_utc(rec.time_partner_purchase)

            worksheet.write(row, 0, stt, header_bold_number)
            worksheet.write(row, 1, rec.product_puchase_id, header_bold_number)
            worksheet.write(row, 2, rec.name_atr)
            worksheet.write(row, 3, date)
            worksheet.write(row, 4, rec.product_qty)
            worksheet.write(row, 5, '{:,}'.format(int(rec.amount_partner_purchase)))
            stt += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()