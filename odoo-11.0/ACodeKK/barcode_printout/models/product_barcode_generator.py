# -*- coding: utf-8 -*-

from odoo import models, fields, api

class product_barcode_generator(models.Model):
    _name = 'product.barcode.generator'

    line_ids = fields.One2many('product.barcode.generator.line', 'generator_id', 'Lines')

    @api.model
    def default_get(self, fields):
        res = super(product_barcode_generator, self).default_get(fields)
        if self._context and self._context.get('active_ids'):
            lines = []
            for product_id in self._context.get('active_ids'):
                product = self.env['product.template'].browse(product_id)
                lines.append({
                    'product_id': product_id,
                    'quantity': product.virtual_available or 0,
                })
            res['line_ids'] = map(lambda x: (0, 0, x), lines)
        return res

    @api.multi
    def action_print(self):
        data = {}
        data['ids'] = self.ids
        # data['docs'] = self
        data['model'] = self._name
        result = self.env['report'].get_action(self, 'barcode_printout.report_product_barcode_generator', data=data)
        result['report_name'] = '%s/%s' %(result['report_name'], self.id)
        return result


class product_barcode_generator_line(models.Model):
    _name = 'product.barcode.generator.line'

    generator_id = fields.Many2one('product.barcode.generator', 'Generator')
    product_id = fields.Many2one('product.template', 'Product', required=True)
    quantity = fields.Integer('Quantity', default=1, required=True)


