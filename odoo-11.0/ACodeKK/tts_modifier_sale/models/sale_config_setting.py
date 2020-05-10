# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    cs_free_delivery = fields.Float(string='Chính sách miễn phí giao hàng',
        help='Chính sách miễn phí giao hàng')

    @api.multi
    def set_cs_free_delivery_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'sale.config.settings', 'cs_free_delivery', self.cs_free_delivery)