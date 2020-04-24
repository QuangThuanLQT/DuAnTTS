# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import math
from odoo import fields, models, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    price_unit_sale_report     = fields.Float(string="Price Unit", compute='_compute_price')
    price_subtotal_sale_report  = fields.Float(string="Price Subtotal", compute='_compute_price')
    price_unit = fields.Float(
        'Unit Price',
        help="Technical field used to record the product cost set by the user during a picking confirmation (when costing "
             "method used is 'average price' or 'real'). Value given in company currency and in product uom.")  # as it's a technical field, we intentionally don't provide the digits attribute

    @api.multi
    def _compute_price(self):
        for record in self:
            if record.group_id and record.group_id.id:
                sale = self.env['sale.order'].search([
                    ('procurement_group_id', '=', record.group_id.id),
                ], limit=1)
                if sale and sale.id:
                    order_line = self.env['sale.order.line'].search([
                        ('order_id', '=', sale.id),
                        ('product_id', '=', record.product_id.id)
                    ], limit=1)
                    if order_line and order_line.id:
                        price_unit = order_line.price_unit
                        if order_line.price_discount:
                            price_unit = order_line.price_discount
                        elif order_line.discount:
                            price_unit = (1 - order_line.discount / 100) * price_unit
                        record.price_unit_sale_report     = price_unit
                        record.price_subtotal_sale_report = order_line.price_subtotal