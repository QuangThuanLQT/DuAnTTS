# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import StringIO
import xlsxwriter



class sale_product_sold_well(models.Model):
    _inherit = 'product.product'


    quantity_sold = fields.Float(digits=(16, 0), compute='get_quantity_sold', store=True)
    amount = fields.Float(digits=(16, 0), compute='get_quantity_sold', store=True)
    name_atr = fields.Char(compute='get_name', string='Product Name')
    trang_thai_hd = fields.Selection([
        ('active', 'Đang kinh doanh'),
        ('unactive', 'Ngừng kinh doanh')
    ], compute='get_trang_thai_hd', string='Trạng thái', store=True)

    @api.depends('active')
    def get_trang_thai_hd(self):
        for rec in self:
            if rec.active:
                rec.trang_thai_hd = 'active'
            else:
                rec.trang_thai_hd = 'unactive'

    @api.depends('stock_move_ids.product_uom_qty', 'list_price')
    def get_quantity_sold(self):
        for rec in self:
            quantity = 0
            line_stock_move = self.env['stock.move'].search(
                [('product_id', '=', rec.id), ('picking_type_id.picking_type', 'in', ['delivery', 'internal_sale']),
                 ('state', '=', 'done')])
            for line in line_stock_move:
                quantity += line.product_uom_qty
            rec.quantity_sold = quantity
            rec.amount = rec.quantity_sold * rec.lst_price

    @api.multi
    def get_name(self):
            for record in self:
                variable_attributes = record.attribute_line_ids.filtered(lambda l: len(l.value_ids) >= 1).mapped(
                    'attribute_id')
                variant = record.attribute_value_ids._variant_name(variable_attributes)
                record.name_atr = variant and "%s - %s" % (record.name, variant) or record.name

    @api.model
    def get_product_list(self):
        product_ids = self.env['product.product'].search([]).with_context({'lang': self.env.user.lang or 'vi_VN'}).mapped('default_code')
        product_list = []
        for product_id in product_ids:
            product_list.append(product_id)
        return product_list

    @api.model
    def get_product_name_search(self, product_name):
        if product_name:
            product_id = self.search([('default_code', '=', product_name)])
            return product_id.ids

    @api.model
    def export_overview_sold_well(self, response):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        sold_ids = self.env['product.product'].search(domain)
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
        worksheet.set_column('D:D', 11)
        worksheet.set_column('E:E', 10)

        summary_header = ['STT', 'Reference', 'Product name', 'Quantity Sold', 'Amount']

        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
        stt = 1

        for rec in sold_ids:
            row += 1

            worksheet.write(row, 0, stt, header_bold_number)
            worksheet.write(row, 1, rec.default_code, header_bold_number)
            worksheet.write(row, 2, rec.name_atr )
            worksheet.write(row, 3, rec.quantity_sold)
            worksheet.write(row, 4, '{:,}'.format(int(rec.amount)))
            stt += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()