# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import base64
from xlrd import open_workbook


class stock_location_ihr(models.Model):
    _inherit = 'stock.location'

    warehouse_id = fields.Many2one('stock.warehouse', compute='_get_warehouse_location', store=True)

    @api.depends('name','location_id')
    def _get_warehouse_location(self):
        for rec in self:
            if rec.display_name:
                warehouse_id = self.env['stock.warehouse'].search([('code', '=', rec.display_name.split('/')[0])],limit=1)
                rec.warehouse_id = warehouse_id

class location_save_product(models.Model):
    _name = 'location.save.product'

    @api.multi
    def open_location_save_product_form(self):
        action = self.env.ref('tts_modifier_inventory.location_save_product_action').read()[0]
        record_location_sale_product = self.env.ref('tts_modifier_inventory.record_location_sale_product')
        for line in record_location_sale_product.line_ids:
            if line.product_id:
                product_id = line.product_id
                location_id = product_id.location_ids
                if location_id:
                    location_id = location_id[0]
                    if line.location_id != location_id:
                        line.location_id = location_id
            else:
                line.unlink()

        product_ids = self.env['product.product'].search([('type', '=', 'product')])
        product_in_save_ids = record_location_sale_product.line_ids.mapped('product_id')
        product_ids = product_ids - product_in_save_ids
        if len(product_ids) > 0:
            for product_id in product_ids:
                location_id = product_id.location_ids
                if location_id:
                    location_id = location_id[0]
                else:
                    location_id = False
                variable_attributes = product_id.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped(
                    'attribute_id')
                variant = product_id.attribute_value_ids._variant_name(variable_attributes)

                name = variant and "%s (%s)" % (product_id.name, variant) or product_id.name
                record_location_sale_product.line_ids += record_location_sale_product.line_ids.new({
                    'product_id': product_id,
                    'default_code': product_id.default_code,
                    'product_sub': name,
                    'attribute_value_ids': ', '.join(
                        product_id.attribute_value_ids.mapped('name')) if product_id.attribute_value_ids else '',
                    'warehouse_id': self.env.ref('stock.warehouse0').id,
                    'location_id' : location_id
                 })
        action['res_id'] = record_location_sale_product.id
        return action

    @api.depends('warehouse_id')
    def _get_line_ids(self):
        product_ids = self.env['product.product'].search([('type', '=', 'product')])
        line_ids = []
        for product_id in product_ids:
            location_id = product_id.location_ids
            if location_id:
                location_id = location_id[0]
            variable_attributes = product_id.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped(
                'attribute_id')
            variant = product_id.attribute_value_ids._variant_name(variable_attributes)

            name = variant and "%s (%s)" % (product_id.name, variant) or product_id.name
            line_ids.append((0, 0, {
                'product_id': product_id,
                'default_code' : product_id.default_code,
                'product_sub': name,
                'attribute_value_ids': ', '.join(product_id.attribute_value_ids.mapped('name')) if product_id.attribute_value_ids else '',
                'warehouse_id' : self.env.ref('stock.warehouse0').id,
                'location_id' : location_id
            }))
        return line_ids

    warehouse_id = fields.Many2one('stock.warehouse',string='Kho',default=lambda self: self.env.ref('stock.warehouse0'))
    line_ids = fields.One2many('location.save.product.line','location_save_product_id', default=_get_line_ids)

    # data_location_id = fields.One2many('location.save.product.line', 'location_save_product_id')
    data_location_save = fields.Binary(string='Data')
    data_location_save_name = fields.Char(string='Data Name')

    @api.multi
    def update_product_location(self):
        for line in self.line_ids:
            if line.product_id and line.location_id:
                if line.location_id not in line.product_id.location_ids:
                    for location_id in line.product_id.location_ids:
                        if location_id.warehouse_id.id == line.location_id.warehouse_id.id:
                            line.product_id.location_ids = [(5, location_id.id)]
                    line.product_id.location_ids = [(4, line.location_id.id)]

    @api.multi
    def import_data_location_save(self):
        # try:
            data = base64.b64decode(self.data_location_save)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)
            rownum = sheet.nrows - 1
            len_lines = len(self.line_ids)
            row_len = rownum if rownum <= len_lines else len_lines
            i = 1
            for line in self.line_ids:
                row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value), sheet.row(i)))
                try:
                    location_save = str(row[1])
                except:
                    location_save = row[1].strip()

                location_save_id = self.env['stock.location'].search([('name', '=', location_save)], limit=1)

                if not location_save_id:
                    raise UserError(str(row[0]) + ' ' + str(row[1]) + ' ' + 'không có trên hệ thống !')

                else:
                    location = {
                        'location_id': location_save_id.id
                    }
                    product = self.env['location.save.product.line'].search([('default_code', '=', str(row[0]))])
                    if product:
                        product.write(location)
                    else:
                        raise UserError(str(row[0]) + ' ' + 'không có trên hệ thống !')
                    i += 1
                    if i > row_len:
                        break
        # except:
        #     raise UserError(str(row[0]) + '' + str(row[1]) + '' + 'không có trên hệ thống !')

    @api.onchange('warehouse_id')
    def onchange_warehouse(self):
        for line in self.line_ids:
            line.warehouse_id = self.warehouse_id
            if line.product_id:
                location_id = line.product_id.location_ids.filtered(
                    lambda l: l.warehouse_id == self.warehouse_id)
                if location_id:
                    line.location_id = location_id[0]

class location_save_product_line(models.Model):
    _name = 'location.save.product.line'

    warehouse_id = fields.Many2one('stock.warehouse', string='Kho')
    product_id = fields.Many2one('product.product',string='Tên')
    default_code = fields.Char(string='Mã nội bộ', readonly=1)
    product_sub = fields.Char(readonly=1,string='Tên')
    attribute_value_ids = fields.Char(string='Thuộc tính', readonly=1)
    location_id = fields.Many2one('stock.location',string='Vị trí lưu trữ', domain=[('usage', '=', 'internal')])
    location_save_product_id = fields.Many2one('location.save.product')



