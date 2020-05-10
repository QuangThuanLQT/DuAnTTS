# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PrintAttribute(models.Model):
    _name = 'prinizi.product.attribute'

    name = fields.Char(required=True)
    type = fields.Selection([('radio', 'Radio'), ('select', 'Select'), ('color', 'Color'),('hidden', 'Hidden')])