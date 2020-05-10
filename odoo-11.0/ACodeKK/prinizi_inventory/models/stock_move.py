# -*- coding: utf-8 -*-

from odoo import models, fields, api

class stock_move_ihr(models.Model):
    _inherit = 'stock.move'

    print_qty = fields.Float(string="Print Qty", digits=(16, 0))