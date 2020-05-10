# -*- coding: utf-8 -*-

from odoo import models, fields, api

class mrp_bom(models.Model):
    _inherit = 'mrp.bom'

    so_id = fields.Many2one('sale.order', 'Sale Order')
    so_line_id = fields.Many2one('sale.order.line', 'Sale Order Line')

    @api.multi
    @api.depends('product_tmpl_id', 'state')
    def name_get(self):
        res = []
        for record in self:
            name = record.product_tmpl_id.name
            if record.state:
                name = '[' + record.state + '] ' + name
            res.append((record.id, name))
        return res