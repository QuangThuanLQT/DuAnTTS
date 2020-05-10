# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime

class product_vendor_price(models.Model):
    _inherit = 'res.partner'

    @api.depends('product_vendors_line')
    def _get_product_vendor_len(self):
        for r in self:
            r.count_list = len(r.product_vendors_line)

    product_vendors_line = fields.One2many('product.vendor.price', 'partner_id')
    count_list = fields.Float(compute='_get_product_vendor_len')

    product_purchase_ids = fields.One2many('product.supplierinfo', 'name', 'Purchased Products')
    count_product = fields.Float(compute='_get_product_purchase_len')

    @api.depends('product_purchase_ids')
    def _get_product_purchase_len(self):
        for r in self:
            r.count_product = len(r.product_purchase_ids)

    @api.multi
    def product_vendor_action_purchase(self):
        purchase_ids = self.mapped('product_purchase_ids')
        action = self.env.ref('modifier_product.product_purchase_action').read()[0]
        action['domain'] = [('id', 'in', purchase_ids.ids)]
        action['context'] = {'visible_product_tmpl_id': False}
        return action

    @api.multi
    def product_vendor_action_mandate(self):

        product_vendors = self.mapped('product_vendors_line')
        action = self.env.ref('modifier_product.product_vendor_action').read()[0]

        if len(product_vendors) >= 1:
            action['domain'] = [('id', 'in', product_vendors.ids)]
        else:
            action['views'] = [(self.env.ref('modifier_product.product_vendor_form_view').id, 'form')]
        return action
