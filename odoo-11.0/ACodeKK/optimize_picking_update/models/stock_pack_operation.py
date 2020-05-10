# -*- coding: utf-8 -*-

from odoo import models, fields, api

class stock_pack_operation(models.Model):
    _inherit = 'stock.pack.operation'

    @api.model
    def create(self, values):
        result = super(stock_pack_operation, self).create(values)
        return result

    @api.multi
    def write(self, values):
        result = super(stock_pack_operation, self).write(values)
        return result