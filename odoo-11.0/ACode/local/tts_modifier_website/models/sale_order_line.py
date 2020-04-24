# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class product_template_order(models.Model):
    _name = "sale.product.template.order"

    product_tmpl_id = fields.Many2one('product.template', string="Product")
    product_qty = fields.Float('Quantity', compute='_compute_qty', store=True)
    amount_untaxed = fields.Float(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all')
    attribute_id = fields.Many2one('product.attribute')
    attribute_value_id = fields.Many2one('product.attribute.value')
    order_line = fields.One2many('sale.order.line', 'product_tmpl_order_id')
    order_id = fields.Many2one('sale.order')

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
            order.update({
                'amount_untaxed': order.order_id.pricelist_id.currency_id.round(amount_untaxed),
            })

    @api.depends('order_line.product_uom_qty')
    def _compute_qty(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            product_qty = 0.0
            for line in order.order_line:
                product_qty += line.product_uom_qty
            order.update({
                'product_qty': product_qty,
            })


class sale_order_line_inhr(models.Model):
    _inherit = "sale.order.line"

    product_tmpl_order_id = fields.Many2one('sale.product.template.order')
    order_id = fields.Many2one('sale.order', required=False)

    def create_product_tmpl_order(self, line):
        product_tmpl_order_id = False
        size_attr_id = self.env['product.attribute'].search(['|' ,('name', '=', 'Size'), ('name', '=', 'size')])
        attribute_ids = line.product_id.product_tmpl_id.mapped('attribute_line_ids').mapped('attribute_id').filtered(lambda att: att not in size_attr_id)
        if attribute_ids:
            for attribute_id in attribute_ids:
                attribute_value_id = line.product_id.attribute_value_ids.filtered(lambda l: l.attribute_id == attribute_id)
                if attribute_value_id:
                    product_tmpl_order_id = self.env['sale.product.template.order'].search(
                        [('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                         ('order_id', '=', line.order_id.id),
                         ('attribute_id', '=', attribute_id.id),
                         ('attribute_value_id', '=', attribute_value_id.id),
                         ], limit=1)
                    if not product_tmpl_order_id:
                        product_tmpl_order_id = self.env['sale.product.template.order'].create({
                            'product_tmpl_id': line.product_id.product_tmpl_id.id,
                            'order_id': line.order_id.id,
                            'attribute_id': attribute_id.id,
                            'attribute_value_id': attribute_value_id.id
                        })
                return product_tmpl_order_id
        else:
            product_tmpl_order_id = self.env['sale.product.template.order'].search(
                [('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                 ('order_id', '=', line.order_id.id),
                 ], limit=1)
            if not product_tmpl_order_id:
                product_tmpl_order_id = self.env['sale.product.template.order'].create({
                    'product_tmpl_id': line.product_id.product_tmpl_id.id,
                    'order_id': line.order_id.id,
                })
        return product_tmpl_order_id

    @api.model
    def create(self, vals):
        res = super(sale_order_line_inhr, self).create(vals)
        if not res.product_tmpl_order_id:
            product_tmpl_order_id = self.create_product_tmpl_order(res)
            res.product_tmpl_order_id = product_tmpl_order_id
        return res
