# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PulsaComponentLine(models.Model):
    _name = 'pulsa.component.line'

    product_tmpl_parent_id = fields.Many2one('product.template')
    product_template_id    = fields.Many2one('product.template', 'Product', required=True)
    balance                = fields.Many2one('product.uom', string='Balance', related='product_template_id.uom_id', readonly=True)