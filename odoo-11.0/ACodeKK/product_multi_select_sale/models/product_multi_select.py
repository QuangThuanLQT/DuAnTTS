# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class product_multi_select(models.Model):
    _name = 'product.multi.select'

    product_ids = fields.Many2many('product.product', string='Products')

    @api.multi
    def add_product_to_line(self):
        for record in self:
            if 'active_id' in self.env.context:
                sales_order_id = self.env['sale.order'].search([('id', '=', self.env.context.get('active_id'))])
                list_product = []
                for product in record.product_ids:
                    list_product.append((0, 0, {
                        'product_id': product.id,
                        'product_uom' : product.uom_id.id
                    }))
                sales_order_id.write({
                    'order_line': list_product
                })