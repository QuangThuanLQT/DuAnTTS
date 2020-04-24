# -*- coding: utf-8 -*-
from odoo import models, fields, api

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    direct_total    = fields.Float('Tổng trực tiếp')

    @api.onchange('direct_total','product_uom_qty')
    def onchange_direct_total(self):
        if self.product_uom_qty and self.direct_total:
            self.price_discount = self.direct_total / self.product_uom_qty