# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class hr_expense(models.Model):
    _inherit = 'hr.expense'

    @api.model
    def get_product_id(self):
        product_general_cost = self.env.ref('cptuanhuy_expense.product_general_cost', raise_if_not_found=False)
        if product_general_cost:
            return product_general_cost.product_variant_id.id

    product_id = fields.Many2one('product.product', string='Product', readonly=True,
                                 states={'draft': [('readonly', False)], 'refused': [('readonly', False)]},
                                 domain=[('can_be_expensed', '=', True)], required=True, default=get_product_id)
