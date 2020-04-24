# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    lot = fields.Many2one('stock.production.lot', 'Lot Number')
