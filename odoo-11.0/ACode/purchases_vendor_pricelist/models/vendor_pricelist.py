# -*- coding: utf-8 -*-

from odoo import models, fields, api


class product_supplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    monthly_discount = fields.Float(string="Chiết khấu tháng(%)")
    bill_price = fields.Float(string="Giá hóa đơn", compute='_get_bill_price', store=True)
    price = fields.Float('Price', default=0.0, compute='_get_price')
    price_add_to_line = fields.Float('Price')

    @api.onchange('price_add_to_line')
    def onchange_price_add_to_line(self):
        for line in self.product_variants_line:
            line.price = self.price_add_to_line

    @api.depends('price', 'monthly_discount')
    def _get_bill_price(self):
        for record in self:
            if record.price:
                bill_price = record.price / (1 - record.monthly_discount * 0.01)
                record.bill_price = bill_price

    @api.depends('product_variants_line.price')
    def _get_price(self):
        for rec in self:
            if rec.product_variants_line:
                rec.price = sum(rec.product_variants_line.mapped('price')) / len(rec.product_variants_line)


class product_variants_line(models.Model):
    _name = 'product.variants.line'

    product_id = fields.Many2one('product.product', string='Product')
    product_name = fields.Char(string='Product', readonly=1, compute="get_attribute_value")
    price = fields.Float()
    line_id = fields.Many2one('product.supplierinfo')
    monthly_discount = fields.Float(string="Chiết khấu tháng(%)", readonly=1)
    bill_price = fields.Float(string="Giá hóa đơn", compute='_get_bill_price', readonly=1)
    attribute_value_ids = fields.Many2many('product.attribute.value', compute="get_attribute_value",
                                           string='Thuộc tính', readonly=1)

    @api.depends('product_id')
    def get_attribute_value(self):
        for rec in self:
            rec.attribute_value_ids = rec.product_id.attribute_value_ids
            rec.product_name = rec.product_id.name

    @api.depends('price', 'monthly_discount')
    def _get_bill_price(self):
        for record in self:
            if record.price:
                bill_price = record.price / (1 - record.monthly_discount * 0.01)
                record.bill_price = bill_price


class vendor_price(models.Model):
    _inherit = 'product.supplierinfo'

    product_variants_line = fields.One2many('product.variants.line', 'line_id')

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        if self.product_tmpl_id:
            if self._context.get('default_product_tmpl_id', False):
                product_variants = self.env['product.product'].search(
                    [('product_tmpl_id', '=', self._context.get('default_product_tmpl_id', False))])
            else:
                product_variants = self.env['product.product'].search(
                    [('product_tmpl_id', '=', self.product_tmpl_id.id)])
            self.product_variants_line = []
            for pro in product_variants:
                line = self.product_variants_line.new({
                    'product_id': pro.id,
                    # 'product_name': pro.name,
                    # 'attribute_value_ids': pro.attribute_value_ids,
                    'price': pro.standard_price,
                    'monthly_discount': self.monthly_discount
                })
                self.product_variants_line += line

    def create_product_supplierinfo_line(self):
        if self.product_tmpl_id:
            product_variants = self.env['product.product'].search(
                [('product_tmpl_id', '=', self.product_tmpl_id.id)])
            self.product_variants_line = []
            for pro in product_variants:
                line = self.product_variants_line.new({
                    'product_id': pro.id,
                    'price': pro.standard_price,
                    'monthly_discount': self.monthly_discount
                })
                self.product_variants_line += line
        return False

    @api.onchange('monthly_discount')
    def _onchange_monthly_discount(self):
        if self.product_tmpl_id:
            for line in self.product_variants_line:
                line.update({
                    'monthly_discount': self.monthly_discount
                })

class product_category_ihr(models.Model):
    _inherit = 'product.category'

    @api.model
    def default_get(self, fields):
        res = super(product_category_ihr, self).default_get(fields)
        res['property_cost_method'] = 'average'
        res['property_valuation'] = 'real_time'
        res['property_stock_account_input_categ_id'] = self.env['account.account'].search(
            [('code', '=', '3381')],
            limit=1).id
        res['property_stock_account_output_categ_id'] = self.env['account.account'].search(
            [('code', '=', '632')],
            limit=1).id
        res['property_stock_valuation_account_id'] = self.env['account.account'].search(
            [('code', '=', '1561')],
            limit=1).id
        return res
