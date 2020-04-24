# -*- coding: utf-8 -*-

from odoo import models, fields, api


class product_template(models.Model):
    _inherit = 'product.template'

    hs_code = fields.Char(string="HS Code", help="Standardized code for international shipping and goods declaration")
    group_id = fields.Char(string="Group Product")
    # group_id = fields.Many2one('product.group', string="Group Product")
    brand_name_select = fields.Char(string='Thương hiệu')
    # brand_name_select = fields.Many2one('brand.name', string='Thương hiệu')
    source_select = fields.Char(string='Xuất xứ')
    # source_select = fields.Many2one('source.name', string='Xuất xứ')
    purchase_code = fields.Char('Mã mua hàng')
    # categ_id = fields.Many2one(
    #     'product.category', 'Internal Category',
    #     change_default=True, default=_get_default_category_id,
    #     required=True, help="Select category for the current product")

    cost_root = fields.Float(compute='_get_cost_root', string="Cost Medium")

    purchase_method = fields.Selection([
        ('purchase', 'On ordered quantities'),
        ('receive', 'On received quantities'),
    ], string="Control Purchase Bills",
        help="On ordered quantities: control bills based on ordered quantities.\n"
             "On received quantities: control bills based on received quantity.", default="receive")

    def _get_cost_root(self):
        for record in self:
            purchase_line_ids = record.env['purchase.order.line'].search(
                [('product_id.product_tmpl_id', '=', record.id), ('order_id.state', '=', 'purchase')])
            amount = 0
            qty = 0
            for line in purchase_line_ids:
                if line.order_id.picking_ids and 'done' in line.order_id.picking_ids.mapped('state'):
                    amount += line.price_discount or line.price_unit
                    qty += 1
            if amount and qty:
                record.cost_root = float(amount / qty)
            else:
                amount = record.standard_price
                qty = 1
                record.cost_root = float(amount / qty)
