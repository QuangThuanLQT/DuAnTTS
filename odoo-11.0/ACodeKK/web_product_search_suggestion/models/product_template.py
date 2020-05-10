# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _


class product_template(models.Model):
    _inherit = "product.template"

    sequence_search = fields.Integer('Sequence')
    keyword_ids = fields.Many2many('product.search.keyword', domain=['|', ('type', '=', 'product'), ('type', '=', 'key')])

