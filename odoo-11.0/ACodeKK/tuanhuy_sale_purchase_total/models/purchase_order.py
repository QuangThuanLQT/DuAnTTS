# -*- coding: utf-8 -*-
from odoo import models, fields, api

class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    direct_total = fields.Float('Tổng trực tiếp')

    @api.onchange('direct_total','product_qty')
    def onchange_direct_total(self):
        if self.product_qty and self.direct_total:
            self.price_discount = self.direct_total / self.product_qty

