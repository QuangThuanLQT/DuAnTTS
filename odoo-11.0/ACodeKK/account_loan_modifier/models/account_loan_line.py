# -*- coding: utf-8 -*-

from odoo import models, fields, api

class account_loan_line(models.Model):
    _inherit = 'account.loan.line'

    date = fields.Date(
        required=True,
        readonly=False,
        help='Date when the payment will be accounted',)

    principal_direct_amount = fields.Monetary(currency_fields='currency_id', string='Số tiền trả gốc trực tiếp')
    direct_amount = fields.Monetary(currency_fields='currency_id',readonly=True,)

    @api.depends('payment_amount', 'interests_amount', 'pending_principal_amount', 'principal_direct_amount')
    def _compute_amounts(self):
        for rec in self:
            rec.final_pending_principal_amount = (rec.pending_principal_amount - rec.payment_amount + rec.interests_amount)
            rec.principal_amount = rec.payment_amount - rec.interests_amount
            if rec.principal_direct_amount:
                rec.principal_amount = rec.principal_direct_amount
                rec.final_pending_principal_amount = rec.pending_principal_amount - rec.principal_direct_amount

    @api.onchange('interests_amount', 'principal_direct_amount')
    def onchange_amount(self):
        self.payment_amount = self.principal_amount + self.interests_amount
        self.rate = (self.interests_amount / self.pending_principal_amount)*100
