# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    journal_entry_count = fields.Integer('# Journal Entry', compute='_compute_journal_entry_count')

    @api.multi
    def _compute_journal_entry_count(self):
        for template in self:
            journal_entry_count = 0
            products = self.env['product.product'].search([('product_tmpl_id', '=', template.id)])
            if len(products) > 0:
                journal_entry_count = self.env['account.move.line'].search([
                    ('product_id', 'in', products.ids)
                ], count=True)
            template.journal_entry_count = journal_entry_count

    @api.multi
    def action_view_journal_entry(self):
        action = self.env.ref('cptuanhuy_accounting.account_move_pnl_report_action').read()[0]
        products = self.env['product.product'].search([('product_tmpl_id', 'in', self.ids)])
        # bom specific to this variant or global to template
        action['context'] = {
            'default_product_tmpl_id': self.ids[0],
            'default_product_id': products.ids[0],
            'search_default_632': True,
            'search_default_511': True,
            'search_default_641': True,
            'search_default_642': True,
            'search_default_811': True,
            'search_default_622': True,
            'search_default_627': True,
        }
        action['domain'] = [('product_id', 'in', [products.ids])]
        return action

    @api.multi
    def calculate_cost_price(self):
        for record in self:
            products = self.env['product.product'].search([
                ('product_tmpl_id','=',record.id)
            ])
            products.calculate_cost_price()