# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class product_template(models.Model):
    _inherit = 'product.template'

    @api.multi
    def write(self, values):
        # if values.get('uom_id', False):
        #     if values.get('uom_po_id', False) and values.get('uom_po_id') != values.get('uom_id'):
        #         raise ValidationError(_('Đơn vị mua hàng và đơn vị tính phải giống nhau'))
        result = super(product_template, self).write(values)
        for record in self:
            if record.uom_id.id != record.uom_po_id.id:
                raise ValidationError(_('Đơn vị mua hàng và đơn vị tính phải giống nhau'))
        return result

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        if len(self) == 1 and len(fields) > 5:
            load = '_classic_write'
        return super(product_template, self).read(fields=fields, load=load)

    @api.model
    def _get_buy_route(self):
        buy_route = self.env.ref('purchase.route_warehouse0_buy', raise_if_not_found=False)
        manufacture_route = self.env.ref('stock.route_warehouse0_mto', raise_if_not_found=False)
        if buy_route and manufacture_route:
            return [buy_route.id, manufacture_route.id]
        if buy_route:
            return buy_route.ids
        return []

    @api.multi
    def update_route_product(self):
        buy_route = self.env.ref('purchase.route_warehouse0_buy', raise_if_not_found=False)
        manufacture_route = self.env.ref('stock.route_warehouse0_mto', raise_if_not_found=False)
        for product in self.search([]):
            product.purchase_method = 'receive'
            if product.route_ids.ids == [buy_route.id, manufacture_route.id]:
                product.route_ids = buy_route
        return True

    @api.multi
    def action_view_stock_moves(self):
        res = super(product_template, self).action_view_stock_moves()
        if res.get('context',False):
            res.get('context', False).update({'search_default_wh_stock': True})
        else:
            res['context'] = {'search_default_wh_stock': True}
        return res

    @api.multi
    @api.constrains('default_code')
    def _space_in_default_code(self):
        for record in self:
            if record.default_code:
                if ' ' in record.default_code:
                    raise ValidationError(_('Mã nội bộ không được chứa khoảng trống'))

    purchase_method = fields.Selection([
        ('purchase', 'On ordered quantities'),
        ('receive', 'On received quantities'),
    ], string="Control Purchase Bills",
        help="On ordered quantities: control bills based on ordered quantities.\n"
             "On received quantities: control bills based on received quantity.", default="receive")

    invoice_policy = fields.Selection(
        [('order', 'Ordered quantities'),
         ('delivery', 'Delivered quantities'),
         ], string='Invoicing Policy',
        help='Ordered Quantity: Invoice based on the quantity the customer ordered.\n'
             'Delivered Quantity: Invoiced based on the quantity the vendor delivered (time or deliveries).',
        default='delivery')

    @api.model
    def default_get(self, fields):
        res = super(product_template, self).default_get(fields)

        res['purchase_method'] = 'receive'
        return res