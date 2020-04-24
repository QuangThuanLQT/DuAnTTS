# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_type          = fields.Selection([
        ('normal', 'Bình Thường'),
        ('pulsa', 'Bán Lẻ'),
    ], string='Loại sản phẩm', default='normal')
    pulsa_component_lines = fields.One2many('pulsa.component.line', 'product_tmpl_parent_id', string='Components')

    @api.onchange('pulsa_component_lines')
    def onchange_pulsa_component_lines(self):
        for product in self:
            if product.pulsa_component_lines:
                product.sale_ok = False
                product.purchase_ok = True