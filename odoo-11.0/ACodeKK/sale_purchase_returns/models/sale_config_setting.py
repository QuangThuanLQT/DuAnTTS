# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    allow_check_expired_date = fields.Selection([
        ('allow', 'Sử dụng'),
        ('unallow', 'Không sử dụng')
    ], 'Kiểm tra hết hạn đổi trả',
        default='allow')

    @api.multi
    def set_allow_check_expired_date_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'sale.config.settings', 'allow_check_expired_date', self.allow_check_expired_date)