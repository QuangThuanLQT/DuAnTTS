# -*- coding: utf-8 -*-
from odoo import fields, models, api

class account_payment(models.Model):
    _inherit = 'account.payment'

    gbn_line = fields.One2many('account.payment.gbn', 'gbn_acc_pay_id')
    payment_count_gbn = fields.Float(compute='_get_gbn_len')
    check_bank_payment = fields.Boolean(compute='_check_bank_payment')

    @api.onchange('journal_id')
    def _check_bank_payment(self):
        if self.journal_id:
            if self.journal_id.name != 'Bank':
                self.check_bank_payment = False
            else:
                self.check_bank_payment = True
        else:
            self.check_bank_payment = False

    @api.depends('gbn_line')
    def _get_gbn_len(self):
        for r in self:
            r.payment_count_gbn = len(r.gbn_line)

    @api.multi
    def account_gbn_action_mandate(self):
        uncs = self.mapped('gbn_line')
        action = self.env.ref('account_gbn.account_gbn_action').read()[0]
        if len(uncs) >= 1:
            action['domain'] = [('id', 'in', uncs.ids)]
        else:
            action['views'] = [(self.env.ref('account_gbn.account_payment_gbn_form').id, 'form')]
        return action

    @api.model
    def default_get(self, fields):
        res = super(account_payment, self).default_get(fields)
        if 'active_id' in self._context:
            acc_pay = False

            if 'active_model' in self._context and self._context['active_model'] == 'account.invoice':
                acc_pay = self.env['account.invoice'].browse(self._context['active_id'])

            if acc_pay:
                for gbn_line in acc_pay.gbn_line:
                    if gbn_line.state == 'done':
                        res['journal_id'] = self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id
                        res['amount'] = gbn_line.amount
                        break
        return res