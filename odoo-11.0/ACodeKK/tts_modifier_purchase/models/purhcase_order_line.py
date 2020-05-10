# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo import SUPERUSER_ID


class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    bill_price = fields.Float(string='Bill Price', digits=dp.get_precision('Product Price'))
    bill_price_subtotal = fields.Monetary(string='Bill Subtotal', store=True)
    price_before_discount = fields.Float(string='Price Unit (before Discount).',
                                         digits=dp.get_precision('Product Price'))
    price_unit_sub = fields.Float('Price Unit', compute='get_price_unit_sub', store=True)
    discount_sub = fields.Float('Discount', compute='get_discount_sub')
    bill_price_sub = fields.Float('Bill Price', compute='get_bill_price_sub')
    tax_id_sub = fields.Float('Tax', compute='get_tax_sub')
    qty_received = fields.Float(digits=(16, 0))

    @api.onchange('product_id')
    def _get_cost_root(self):
        for record in self:
            if record.product_id:
                record.tax_sub = record.order_id.purchase_tax
                record.cost_root = 0

    @api.multi
    def _get_stock_move_price_unit(self):
        self.ensure_one()
        line = self[0]
        order = line.order_id
        price_unit = line.price_unit
        if line.taxes_id:
            price_unit = line.taxes_id.with_context(round=False).compute_all(
                price_unit, currency=line.order_id.currency_id, quantity=1.0, product=line.product_id,
                partner=line.order_id.partner_id
            )['total_excluded']
        if line.product_uom.id != line.product_id.uom_id.id:
            price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
        if order.currency_id != order.company_id.currency_id:
            price_unit = order.currency_id.compute(price_unit, order.company_id.currency_id, round=False)
        return price_unit

    @api.depends('discount', 'price_before_discount')
    def get_price_unit_sub(self):
        for line in self:
            line.price_unit_sub = line.price_before_discount * (100 - line.discount) / 100

    @api.onchange('discount', 'price_before_discount')
    def onchange_price_before_discount(self):
        for line in self:
            line.price_unit = line.price_unit_sub

    @api.depends('discount')
    def get_discount_sub(self):
        for line in self:
            line.discount_sub = line.discount

    @api.depends('bill_price')
    def get_bill_price_sub(self):
        for line in self:
            line.bill_price_sub = line.bill_price

    @api.depends('tax_sub')
    def get_tax_sub(self):
        for line in self:
            line.tax_id_sub = line.tax_sub

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.order_id.state != 'purchase':
            result = {}
            if not self.product_id:
                return result

            # Reset date, price and quantity since _onchange_quantity will provide default values
            self.date_planned = self.order_id.date_order or datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            self.price_unit = self.product_id.standard_price if self.product_id.standard_price else 1
            self.price_before_discount = self.product_id.standard_price if self.product_id.standard_price else 1
            self.product_qty = 0.0
            self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
            result['domain'] = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}

            product_lang = self.product_id.with_context(
                lang=self.partner_id.lang,
                partner_id=self.partner_id.id,
            )
            self.name = product_lang.display_name
            if product_lang.description_purchase:
                self.name += '\n' + product_lang.description_purchase

            fpos = self.order_id.fiscal_position_id
            if self.env.uid == SUPERUSER_ID:
                company_id = self.env.user.company_id.id
                self.taxes_id = fpos.map_tax(
                    self.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
            else:
                self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id)

            if self.order_id.tax_id and self.order_id.tax_id.id:
                self.tax_sub = int(self.order_id.tax_id.amount)
                self.taxes_id = self.order_id.tax_id

            self._suggest_quantity()
            self._onchange_quantity()

            return result
        else:
            self.name = self.product_id.name
            if self.product_id.description_sale:
                self.name += '\n' + self.product_id.description_sale

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        if not self.product_id:
            return

        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order[:10],
            uom_id=self.product_uom)

        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not seller:
            return
        product_seller = seller.product_variants_line.filtered(lambda r: r.product_id == self.product_id)
        price_unit = self.env['account.tax']._fix_tax_included_price_company(product_seller.price,
                                                                             self.product_id.supplier_taxes_id,
                                                                             self.taxes_id,
                                                                             self.company_id) if seller else 0.0
        price_before_discount = price_unit
        if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
            price_unit = seller.currency_id.compute(price_unit, self.order_id.currency_id)
            price_before_discount = price_unit

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)
            price_before_discount = price_unit
        if self.product_id and self.purchase_order_return == True:
            price_unit = self.product_id.get_history_price(self.product_id.company_id.id,
                                                           self.date_order or datetime.now())
        self.price_unit = price_unit
        self.price_before_discount = price_before_discount

    @api.onchange('product_id', 'product_qty', 'product_uom')
    def _bill_onchange_quantity(self):
        if not self.product_id:
            return
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order[:10],
            uom_id=self.product_uom)

        if not seller:
            return
        product_seller = seller.product_variants_line.filtered(lambda r: r.product_id == self.product_id)
        if product_seller:
            self.bill_price = product_seller.bill_price
            self.discount = product_seller.monthly_discount

    @api.multi
    def check_supplier_price(self, price):
        supplierinfo_model = self.env['product.supplierinfo']
        for record in self:
            order = record.order_id or False
            if order and order.id and not order.purchase_order_return:
                if order.partner_id and order.partner_id.id:
                    seller_price = supplierinfo_model.search([
                        ('name', '=', order.partner_id.id),
                        ('product_tmpl_id', '=', record.product_id.product_tmpl_id.id),
                    ], limit=1)
                    if seller_price and seller_price.id:
                        seller_price.price = price
                    else:

                        sellerinfor = {
                            'name': order.partner_id.id,
                            'price': price,
                            'product_tmpl_id': record.product_id.product_tmpl_id.id,
                            # 'product_id': record.product_id.id
                        }
                        id = supplierinfo_model.create(sellerinfor)
                        id.onchange_product_tmpl_id()

    @api.constrains('product_id', 'product_qty')
    def product_id_qty_for_quotation(self):
        for record in self:
            if record.order_id.state in ['draft', 'sent']:
                if record.product_id and record.order_id.purchase_order_return:
                    if record.product_qty > (record.product_id.sp_co_the_ban + record.product_qty):
                        raise ValidationError(
                            _('Bạn định trả %s sản phẩm %s nhưng chỉ có %s sản phẩm có thể trả hàng!' % (
                                record.product_qty, record.product_id.display_name,
                                record.product_id.sp_co_the_ban + record.product_qty)))
            else:
                if record.product_id and record.order_id.purchase_order_return:
                    dest_location = self.env.ref('stock.stock_location_customers')
                    value = sum(self.env['stock.move'].search([('product_id', '=', record.product_id.id),
                                                               ('location_dest_id', '=', dest_location.id or False),
                                                               ('purchase_line_id', '=', record.id),
                                                               ('state', 'not in', ['done', 'cancel'])]).mapped(
                        'product_uom_qty'))
                    if record.product_qty > (record.product_id.sp_co_the_ban + value):
                        raise ValidationError(
                            _('Bạn định trả %s sản phẩm %s nhưng chỉ có %s sản phẩm có thể trả hàng!' % (
                                record.product_qty, record.product_id.display_name,
                                record.product_id.sp_co_the_ban)))
