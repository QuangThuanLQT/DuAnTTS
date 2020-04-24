# -*- coding: utf-8 -*-
from odoo import fields, models, api

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    gbn_line = fields.One2many('account.payment.gbn', 'gbn_acc_inv_id')

    @api.multi
    def account_invoice_action_mandate_gbn(self):
        gbns = self.mapped('gbn_line')
        action = self.env.ref('account_gbn.account_gbn_action').read()[0]
        if len(gbns) >= 1:
            action['domain'] = [('gbn_acc_inv_id', '=', self.id)]
        else:
            action['views'] = [(self.env.ref('account_gbn.account_payment_gbn_form').id, 'form')]
        action['context'] = "{'default_acc_inv_id': '%s','status':'%s'}" % (self.id,self.state)
        return action

    @api.depends('gbn_line')
    def _get_gbn_len(self):
        for r in self:
            r.mandate_count_gbn = len(r.gbn_line)

    mandate_count_gbn = fields.Float(compute='_get_gbn_len')