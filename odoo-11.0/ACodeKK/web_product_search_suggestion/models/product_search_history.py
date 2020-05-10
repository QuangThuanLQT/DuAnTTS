# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class product_search_history(models.Model):
    _name = "product.search.history"

    keyword_id = fields.Many2one('product.search.keyword')
    key = fields.Char()
    user_id = fields.Many2one('res.users')
    product_id = fields.Many2one('product.product')
    product_tmpl_id = fields.Many2one('product.template')
    date = fields.Datetime('Date')

