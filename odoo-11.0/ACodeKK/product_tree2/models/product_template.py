# -*- coding: utf-8 -*-

import time
import math

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    parent_categ_id = fields.Many2one('product.category', 'Parent Product Category', related='categ_id.parent_id')

class ProductCategory(models.Model):
    _inherit = "product.category"

    product_ids = fields.Many2many('product.template', string="Products", compute="_compute_products")

    @api.multi
    def _compute_products(self):
        for record in self:
            product_ids = self.env['product.template'].search([])
            record.product_ids = product_ids.ids