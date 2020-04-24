# -*- coding: utf-8 -*-

from odoo import models, fields, api


class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm_order(self):
        res = super(sale_order, self).action_confirm_order()
        for order in self:
            order.confirmation_date = fields.Datetime.now()
        return res