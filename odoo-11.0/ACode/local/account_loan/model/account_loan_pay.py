# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _

class AccountLoanPay(models.Model):
    _name = 'account.loan.pay'

    name = fields.Char('Description')
    loan_id = fields.Many2one(
        'account.loan',
        required=True,
        # readonly=True,
        ondelete='cascade',
    )
    pay_id = fields.Many2one(
        'account.loan',
        required=True,
        # readonly=True,
        string='Pay',
        ondelete='cascade',
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='loan_id.currency_id',
    )
    amount = fields.Monetary('Amount')

    @api.onchange('pay_id')
    def onchange_pay_id(self):
        for record in self:
            if record.pay_id:
                record.amount = record.pay_id.pending_principal_amount