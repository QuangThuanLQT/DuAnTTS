# -*- coding: utf-8 -*-

from odoo import models, fields, api

class res_partner(models.Model):
    _inherit = 'res.partner'

    loan_total_fund      = fields.Float('Loan Total Fund', compute='_compute_loan')
    loan_total_credit    = fields.Float('Loan Total Credit', compute='_compute_loan')
    loan_available       = fields.Float('Loan Available', compute='_compute_loan_available')
    loan_available_asset = fields.Float('Loan Asset Available', compute='_compute_loan_available')

    @api.multi
    def _compute_loan_available(self):
        for record in self:
            record.loan_available       = record.loan_limit - record.loan_total_fund - record.loan_total_credit
            record.loan_available_asset = record.loan_limit_asset - record.loan_total_fund - record.loan_total_credit

    @api.multi
    def _compute_loan(self):
        for record in self:
            total_fund = 0
            total_credit = 0
            loans = self.env['account.loan'].search([
                ('partner_id', '=', record.id),
                ('state', '=', 'posted')
            ])
            for loan in loans:
                total_fund   += loan.loan_fund
                total_credit += loan.loan_credit

            record.loan_total_fund   = total_fund
            record.loan_total_credit = total_credit