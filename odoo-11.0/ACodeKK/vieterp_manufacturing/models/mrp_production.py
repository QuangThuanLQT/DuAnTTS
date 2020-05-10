# -*- coding: utf-8 -*-

from odoo import models, fields, api

class mrp_bom(models.Model):
    _inherit = 'mrp.production'

    so_id = fields.Many2one('sale.order', 'Sale Order')
    so_line_id = fields.Many2one('sale.order.line', 'Sale Order Line')
    mo_date = fields.Date('Manufacturing Date')