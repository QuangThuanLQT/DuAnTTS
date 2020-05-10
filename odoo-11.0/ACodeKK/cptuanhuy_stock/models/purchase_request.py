# -*- coding: utf-8 -*-

from odoo import models, fields, api

class purchase_request_line(models.Model):
    _inherit = 'purchase.request.line'

    stock_move_id = fields.Many2one('stock.move')
