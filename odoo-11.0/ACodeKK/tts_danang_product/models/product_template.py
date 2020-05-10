# -*- coding: utf-8 -*-

from odoo import models, fields, api

class product_template(models.Model):
    _inherit = 'product.template'

    default_code = fields.Char(readonly=False, track_visibility='onchange')
