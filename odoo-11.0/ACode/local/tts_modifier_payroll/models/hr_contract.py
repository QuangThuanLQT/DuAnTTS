# -*- coding: utf-8 -*-

from odoo import models, fields, api

class hr_contract(models.Model):
    _inherit = 'hr.contract'

    wage_insurance = fields.Float(string='Wage Insurance', required=True)