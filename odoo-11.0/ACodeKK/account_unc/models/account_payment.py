# -*- coding: utf-8 -*-
from odoo import fields, models, api

class account_payment(models.Model):
    _inherit = 'account.payment'


    @api.depends('unc_line')
    def _get_unc_len(self):
        for r in self:
            r.payment_count = len(r.unc_line)

    unc_line = fields.One2many('account.payment.unc', 'acc_pay_id')
    payment_count = fields.Float(compute='_get_unc_len')

    @api.multi
    def account_unc_action_mandate(self):
        uncs = self.mapped('unc_line')
        action = self.env.ref('account_unc.account_unc_action').read()[0]
        if len(uncs) >= 1:
            action['domain'] = [('id', 'in', uncs.ids)]
        else:
            action['views'] = [(self.env.ref('account_unc.mandate_form_view').id, 'form')]
        return action

    @api.model
    def default_get(self, fields):
        res = super(account_payment, self).default_get(fields)
        if 'active_id' in self._context:
            acc_pay = False

            if 'active_model' in self._context and self._context['active_model'] == 'account.invoice':
                acc_pay = self.env['account.invoice'].browse(self._context['active_id'])

            if acc_pay:
                for unc_line in acc_pay.unc_line:
                    if unc_line.state == 'done':
                        res['journal_id'] = self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id
                        res['amount'] = unc_line.amount
                        break
        return res