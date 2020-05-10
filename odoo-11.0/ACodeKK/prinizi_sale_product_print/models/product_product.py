# -*- coding: utf-8 -*-

from odoo import models, fields, api

class product_template_ihr(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, val):
        res = super(product_template_ihr, self).create(val)
        res.create_product_print()
        return res

    @api.multi
    def write(self, val):
        res = super(product_template_ihr, self).write(val)
        if 'attribute_line_ids' in val:
            self.create_product_print()
        return res

    @api.multi
    def unlink(self):
        res = super(product_template_ihr, self).unlink()
        for rec in self:
            product_print_ids = self.env['product.print'].search([('product_id', '=',rec.id)])
            product_print_ids.unlink()
        return res

    @api.multi
    def create_product_print(self):
        for rec in self:
            attribute_line_ids = rec.attribute_line_ids.filtered(lambda l: l.attribute_id.name in ('Màu','màu','Mau','mau'))
            product_print_ids = self.env['product.print'].search([('product_id', '=', rec.id)]).mapped('attribute_value_id')
            for attribute_line_id in attribute_line_ids:
                for value_id in attribute_line_id.value_ids:
                    if value_id not in product_print_ids:
                        self.env['product.print'].create({
                            'product_id': rec.id,
                            'attribute_value_id' : value_id.id,
                        })