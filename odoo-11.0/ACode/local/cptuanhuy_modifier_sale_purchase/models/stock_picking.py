# -*- coding: utf-8 -*-

from odoo import models, fields, api

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def create(self, values):
        result = super(stock_picking, self).create(values)
        return result