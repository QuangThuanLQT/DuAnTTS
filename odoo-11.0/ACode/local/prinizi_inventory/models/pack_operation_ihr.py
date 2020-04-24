# -*- coding: utf-8 -*-

from odoo import models, fields, api


class pack_operation_ihr(models.Model):
    _inherit = 'stock.pack.operation'

    print_qty = fields.Float(string="Print Qty",digits=(16, 0))
