# -*- coding: utf-8 -*-

from odoo import models, fields, api

class task(models.Model):
    _inherit = 'project.task'

    description_task = fields.Text(string="Description")
    team_task = fields.Char(string="Team")
    start_date_task = fields.Date(string="Start Date")
    end_date_task = fields.Date(string="End Date")
    priority_task = fields.Selection([('low', 'Low'),('medium', 'Medium'),('high', 'High')],string='Priority')
