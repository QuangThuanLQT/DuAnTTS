# -*- coding: utf-8 -*-

from odoo import models, fields, api

class okr(models.Model):
    _name = 'okr'

    name = fields.Char(string="Name")
    start_date = fields.Date(string="Start date")
    end_date = fields.Date(string="End date")
    objectives = fields.One2many('objectives','okr_id', string="Objectives")

class objectives(models.Model):
    _name = 'objectives'

    name = fields.Char(string="Name")
    owner = fields.Many2one('hr.employee', string="Owner")
    due_date = fields.Date(string="Due date")
    key_results = fields.One2many('key.results','objective_id', string="Key Results")
    key_results_sub = fields.Char(string="Key Results", compute = "get_key_results", store=True)
    okr_id = fields.Many2one('okr')

    @api.depends('key_results')
    def get_key_results(self):
        for rec in self:
            if rec.key_results:
                rec.key_results_sub = ','.join(rec.key_results.mapped('name'))

class key_results(models.Model):
    _name = 'key.results'

    name = fields.Char(string="Name")
    objective_id = fields.Many2one('objectives')
