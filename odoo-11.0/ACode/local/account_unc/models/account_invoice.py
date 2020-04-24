# -*- coding: utf-8 -*-
from odoo import fields, models, api

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    unc_line = fields.One2many('account.payment.unc', 'acc_inv_id')

    @api.multi
    def account_invoice_action_mandate(self):
        uncs = self.mapped('unc_line')
        action = self.env.ref('account_unc.account_unc_action').read()[0]
        if len(uncs) >= 1:
            action['domain'] = [('acc_inv_id', '=', self.id)]
        else:
            action['views'] = [(self.env.ref('account_unc.mandate_form_view').id, 'form')]
        action['context'] = "{'default_acc_inv_id': '%s','status':'%s'}" % (self.id,self.state)
        return action

    @api.depends('unc_line')
    def _get_unc_len(self):
        for r in self:
            r.mandate_count = len(r.unc_line)

    mandate_count = fields.Float(compute='_get_unc_len')