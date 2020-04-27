# -*- coding: utf-8 -*-

from odoo import models, fields, api


class products(models.Model):
    _inherit = 'product.template'

class product_variants(models.Model):
    _inherit = 'product.product'

