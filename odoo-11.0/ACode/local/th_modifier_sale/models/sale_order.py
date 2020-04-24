# -*- coding: utf-8 -*-

from odoo import models, fields, api

class button_click(models.Model):
    _inherit = 'sale.order'

    record_checked_xhd = fields.Boolean(string='Xuất hoá đơn')

    @api.multi
    def change_record_button_checked(self):
        for record in self:
            if not record.record_checked_xhd:
                record.record_checked_xhd = True
            else:
                record.record_checked_xhd = False

