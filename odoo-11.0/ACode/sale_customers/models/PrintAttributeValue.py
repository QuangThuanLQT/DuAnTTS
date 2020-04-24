# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PrintAttributeValue(models.Model):
    _name = 'prinizi.product.attribute.value'
    _order = 'sequence'

    attribute = fields.Many2one('prinizi.product.attribute', required=True)
    name = fields.Char(required=True)
    sequence = fields.Integer('Sequence', help="Determine the display order")
    phi_in = fields.Float()
    he_so_dien_tich = fields.Float()
