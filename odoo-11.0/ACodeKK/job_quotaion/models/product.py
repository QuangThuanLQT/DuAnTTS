# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

class product_child_select(models.TransientModel):
    _name = 'product.child.select'

    domain = fields.Char()
    product_ids = fields.Many2many('product.product', string='Linh kiện')

    @api.model
    def default_get(self, fields):
        res = super(product_child_select, self).default_get(fields)
        if 'domain' in self._context and self._context['domain']:
            res['domain'] = self._context['domain']
        return res

    @api.onchange('domain')
    def onchange_domain(self):
        if 'domain' in self._context and self._context['domain']:
            return {
                'domain': {
                    'product_ids': [('id', 'in', self._context['domain'])]
                }
            }
        else:
            return {
                'domain': {
                    'product_ids': [('id', 'in', [])]
                }
            }

    @api.multi
    def add_product_to_line(self):
        if 'active_id' in self._context and self._context['active_id']:
            line = self.env['job.quotaion.line'].browse(self._context['active_id'])
            line.product_child_ids = self.product_ids


class product_template_child(models.Model):
    _name = 'product.template.child'

    parent_id = fields.Many2one('product.template', string='Parent')
    product_id = fields.Many2one('product.template', string='Sản phẩm', required=True)
    list_price = fields.Float(related='product_id.list_price', string='Giá bán', readonly=True, store=True)
    default_code = fields.Char(related='product_id.default_code', string='Mã nội bộ', readonly=True, store=True)
    brand_name = fields.Many2one('brand.name', 'Thương hiệu', related='product_id.brand_name_select', readonly=True, store=True)
    source_name = fields.Many2one('source.name', 'Xuất xứ', related='product_id.source_select', readonly=True, store=True)


class product_template(models.Model):
    _inherit = 'product.template'


    child_ids = fields.One2many('product.template.child', 'parent_id', string='Phụ kiện')
