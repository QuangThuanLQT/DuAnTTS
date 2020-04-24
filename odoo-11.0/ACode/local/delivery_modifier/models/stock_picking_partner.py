# -*- coding: utf-8 -*-

from odoo import models, fields, api

class stock_picking_partner(models.Model):
    _inherit = 'stock.picking'

    delivery_id = fields.Many2one('res.partner', 'Người giao', required=True)
    receive_id = fields.Many2one('res.partner', 'Người nhận', required=True)

