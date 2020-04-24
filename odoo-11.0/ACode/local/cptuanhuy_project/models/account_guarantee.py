# -*- coding: utf-8 -*-
from odoo import models, fields, api

class account_guarantee(models.Model):
    _inherit = 'account.guarantee'

    project_id      = fields.Many2one('project.project',string='Dự án',required=False)