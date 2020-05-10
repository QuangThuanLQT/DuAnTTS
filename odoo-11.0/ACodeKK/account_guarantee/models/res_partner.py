# -*- coding: utf-8 -*-

from odoo import models, fields, api

class res_partner(models.Model):
    _inherit = 'res.partner'

    guarantee_total_fund      = fields.Float('Guarantee Total Fund', compute='_compute_guarantee')
    guarantee_total_credit    = fields.Float('Guarantee Total Credit', compute='_compute_guarantee')
    guarantee_available       = fields.Float('Guarantee Available', compute='_compute_guarantee_available')
    guarantee_available_asset = fields.Float('Guarantee Asset Available', compute='_compute_guarantee_available')

    @api.multi
    def _compute_guarantee_available(self):
        for record in self:
            record.guarantee_available       = record.guarantee_limit - record.guarantee_total_fund - record.guarantee_total_credit
            record.guarantee_available_asset = record.guarantee_limit_asset - record.guarantee_total_fund - record.guarantee_total_credit

    @api.multi
    def _compute_guarantee(self):
        for record in self:
            total_fund = 0
            total_credit = 0
            guarantees = self.env['account.guarantee'].search([
                ('partner_id', '=', record.id),
                ('state', '=', 'done')
            ])
            for guarantee in guarantees:
                total_fund   += guarantee.guarantee_fund
                total_credit += guarantee.guarantee_credit

            record.guarantee_total_fund   = total_fund
            record.guarantee_total_credit = total_credit