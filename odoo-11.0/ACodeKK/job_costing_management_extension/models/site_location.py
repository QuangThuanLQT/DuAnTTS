from odoo import models, fields, api

class StockLocation(models.Model):
	_inherit = 'stock.location'

	site_loc = fields.Many2one('project.project')