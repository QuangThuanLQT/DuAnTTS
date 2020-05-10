# -*- coding: utf-8 -*-

from odoo import models, fields, api

class mrp_bom(models.Model):
    _inherit = ['mrp.bom', 'mail.thread']
    _name = 'mrp.bom'

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
