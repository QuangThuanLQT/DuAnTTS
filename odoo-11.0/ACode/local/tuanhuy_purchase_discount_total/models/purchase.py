from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = amount_discount = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty,
                                                      product=line.product_id, partner=line.order_id.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
                if line.price_discount:
                    amount_discount += (line.product_qty * (line.price_unit - line.price_discount))
                else:
                    amount_discount += (line.product_qty * line.price_unit * line.discount) / 100
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_discount': order.currency_id.round(amount_discount),
                'amount_total': amount_untaxed + amount_tax,
            })

    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], string='Discount type',
                                     readonly=True,
                                     states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                     default='percent')
    discount_rate = fields.Float('Discount Rate', digits_compute=dp.get_precision('Account'),
                                 readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',
                                     track_visibility='always',digits=(16,0))
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all',digits=(16,0))
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all',digits=(16,0))
    amount_discount = fields.Monetary(string='Discount', store=True, readonly=True, compute='_amount_all',track_visibility='always',digits=(16,0))

    @api.onchange('discount_type', 'discount_rate', 'order_line')
    def supply_rate(self):
        for order in self:
            if order.discount_rate:
                if order.discount_type == 'percent':
                    for line in order.order_line:
                        line.discount = order.discount_rate
                else:
                    total = discount = 0.0
                    for line in order.order_line:
                        total += round((line.product_qty * line.price_unit))
                    if order.discount_rate != 0:
                        discount = (order.discount_rate / total) * 100
                    else:
                        discount = order.discount_rate
                    for line in order.order_line:
                        line.discount = discount

class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    discount = fields.Float(digits=(16, 2), default=0.0)
    price_discount = fields.Monetary(digits=(16, 2))
    cost_root = fields.Float(compute='_get_cost_root', string="Cost Medium")

    @api.onchange('product_id')
    def _get_cost_root(self):
        for record in self:
            if record.product_id:
                record.cost_root = record.product_id.cost_root

    @api.depends('product_qty', 'price_unit', 'taxes_id','discount','price_discount')
    def _compute_amount(self):
        for line in self:

            if line.price_discount:
                price = line.price_discount
                taxes_id = line.taxes_id
            else:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes_id = line.taxes_id

            taxes = taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty,
                                              product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.onchange('discount')
    def line_onchange_discount(self):
        if self.discount and self.price_unit and not self.price_discount:
            self.price_discount = self.price_unit - (self.discount * self.price_unit / 100)

    @api.onchange('price_discount')
    def line_onchange_price_discount(self):
        if self.price_unit and self.price_discount:
            self.discount = (self.price_unit - self.price_discount) / self.price_unit * 100