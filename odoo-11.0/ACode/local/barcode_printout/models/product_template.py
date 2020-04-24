# -*- coding: utf-8 -*-

from odoo import models, fields, api

class product_template(models.Model):
    _inherit = 'product.template'

    barcode_label = fields.Char('Barcode Label', compute='_compute_barcode_label')

    @api.depends('barcode', 'default_code')
    def _compute_barcode_label(self):
        for record in self:
            barcode_label = ''
            if record.barcode and record.default_code:
                barcode_label = '%s-%s' %(record.barcode, record.default_code)
            elif record.default_code:
                barcode_label = '%s-%s' % (record.barcode, record.default_code)
            barcode_label = barcode_label.replace('/', '')
            record.barcode_label = barcode_label

    @api.model
    def create(self, values):
        if not values.get('barcode', False):
            barcode = self.env['ir.sequence'].next_by_code('product.template.barcode') or '/'
            values['barcode'] = barcode
        return super(product_template, self).create(values)

    @api.model
    def fill_barcode(self):
        products = self.search([], order='id asc')
        products.fill_multi_barcode()
        return True

    @api.multi
    def fill_multi_barcode(self):
        for record in self:
            if not record.barcode:
                barcode = self.env['ir.sequence'].next_by_code('product.template.barcode') or '/'
                record.barcode = barcode
                self.env.cr.commit()
        return True