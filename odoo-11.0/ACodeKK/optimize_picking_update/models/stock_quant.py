# -*- coding: utf-8 -*-

from odoo import models, fields, api

class stock_quant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def create(self, values):
        result = super(stock_quant, self).create(values)
        return result

    @api.multi
    def write(self, values):
        result = super(stock_quant, self).write(values)
        return result