# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
	_inherit = 'res.partner'

	is_subcontractor = fields.Boolean('Is Sub Contractor')
	sub_contractor_project_id = fields.Many2many('project.project')