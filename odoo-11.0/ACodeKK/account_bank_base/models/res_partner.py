# -*- coding: utf-8 -*-

from odoo import models, fields, api

class res_partner(models.Model):
    _inherit = 'res.partner'

    bank                  = fields.Boolean('Is a Bank', default=False)
    bank_type             = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External')
    ], 'Bank Type', default='external')
    loan_limit            = fields.Float('Loan Limit')
    loan_limit_asset      = fields.Float('Loan Limit Asset')
    guarantee_limit       = fields.Float('Guarantee Limit')
    guarantee_limit_asset = fields.Float('Guarantee Limit Asset')
    asset_estimate_total  = fields.Float('Asset Estimate Total', compute='_compute_asset_total')

    @api.multi
    def _compute_asset_total(self):
        for record in self:
            total = 0
            estimates = self.env['bank.estimate'].search([
                ('partner_id', '=', record.id),
                ('state', '=', 'hold')
            ])
            for estimate in estimates:
                total += estimate.estimate_value
            record.asset_estimate_total = total