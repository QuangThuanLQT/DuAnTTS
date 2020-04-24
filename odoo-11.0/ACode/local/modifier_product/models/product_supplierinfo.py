# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime

class product_supplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    product_price_id = fields.Many2one('product.vendor.price', required=False, ondelete='cascade', index=True, copy=False)
    brand = fields.Char(string='brand')
    made_in = fields.Char(string='made in')
    listed_price = fields.Float(string='listed price')

    @api.onchange('date_start')
    def _onchange_date_from(self):
        if self.product_price_id:
            self.date_start = self.product_price_id.date_from
            self.date_end = self.product_price_id.date_to
            self.name = self.product_price_id.partner_id.id
