# -*- coding: utf-8 -*-

from odoo import models, fields, api

class project_project_inherit(models.Model):
    _inherit = 'project.project'

    analytic_account_ids = fields.One2many('account.analytic.account','project_id')

    @api.multi
    def action_contract(self):
        self.write({'state': 'contract'})
        if self.analytic_account_id:
            self.analytic_account_id.write({
                'is_project' : True,
                'fix_price_invoices' : True,
                'amount_max' : self.project_value,
                'partner_id' : self.partner_id.id,
                'state' : 'draft',
                'project_id' : self.id,
            })

            return {'type': 'ir.actions.act_window',
                    'res_model': 'account.analytic.account',
                    'view_mode': 'form',
                    'res_id': self.analytic_account_id.id,
                    'target': 'current'}

    @api.multi
    def button_cancel(self):
        super(project_project_inherit, self).button_cancel()
        self.analytic_account_id.is_project = False
        self.analytic_account_id.amount_max = 0.0
        self.analytic_account_id.write({
            'is_project' : False,
            'amount_max' : 0.0,
            'state' : 'cancel',
            'project_id': False,
        })