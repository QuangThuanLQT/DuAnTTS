# -*- coding: utf-8 -*-

from odoo import models, fields, api

class product_pricelist(models.Model):
    _inherit = 'product.pricelist'

    state = fields.Selection([
        ('draft', "Draft"),
        ('confirmed', "Confirmed"),
        ('done', "Done"),
    ], default='draft', string='Status')

    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_confirm(self):
        self.state = 'confirmed'

    @api.multi
    def action_done(self):
        self.state = 'done'