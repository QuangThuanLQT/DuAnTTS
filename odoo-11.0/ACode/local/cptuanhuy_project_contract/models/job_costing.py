# -*- coding: utf-8 -*-

from odoo import models, fields, api

class job_costing_inherit(models.Model):
    _inherit = 'job.costing'

    contract_count = fields.Integer(string="Hợp đồng", compute="_get_contract_count")

    def _get_contract_count(self):
        for record in self:
            contract_ids = record.project_id.analytic_account_id.filtered(lambda ct: ct.is_project == True)
            record.contract_count = len(contract_ids)

    @api.multi
    def action_open_contract(self):
        contract_ids = self.project_id.analytic_account_id.filtered(lambda ct: ct.is_project == True)
        action = self.env.ref('stable_account_analytic_analysis.action_account_analytic_overdue_all').read()[0]
        action['domain'] = [('id', 'in', contract_ids.ids)]
        return action
