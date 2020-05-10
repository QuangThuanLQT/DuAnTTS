# -*- coding: utf-8 -*-

from odoo import models, fields, api

class account_invoice_ihr(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_open(self):
        res = super(account_invoice_ihr, self.with_context(from_cptuanhuy=True)).action_invoice_open()
        return res

