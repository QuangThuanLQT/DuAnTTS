# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError


class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    @api.constrains('product_id', 'product_qty')
    def product_id_qty_for_quotation(self):
        for record in self:
            stock_location = self.env.ref('stock.stock_location_stock')
            if record.order_id.state in ['draft', 'sent']:
                if record.product_id and record.order_id.purchase_order_return:
                    if record.order_id.location_return == 'normal':
                        if record.order_id.location_id == stock_location:
                            if record.product_qty > (record.product_id.sp_co_the_ban + record.product_qty):
                                raise ValidationError(
                                    _('Bạn định trả %s sản phẩm %s nhưng chỉ có %s sản phẩm có thể trả hàng!' % (
                                        record.product_qty, record.product_id.display_name,
                                        record.product_id.sp_co_the_ban + record.product_qty)))
                        else:
                            qty_available = record.product_id.with_context(location=record.order_id.location_id.id,
                                                                         location_id=record.order_id.location_id.id).qty_available
                            sp_ban_chua_giao = record.product_id.with_context(location=record.order_id.location_id.id,
                                                                            location_id=record.order_id.location_id.id).sp_ban_chua_giao
                            if record.product_qty > (qty_available - sp_ban_chua_giao):
                                raise ValidationError(_('Không đủ hàng để trả. Chỉ có %s sản phẩm %s trong %s.' % (
                                    (qty_available - sp_ban_chua_giao), record.product_id.display_name, record.order_id.location_id.display_name)))
                    elif record.order_id.location_return == 'damaged':
                        location_id = record.order_id.location_id
                        qty = record.product_id.with_context(location=location_id.id,
                                                           location_id=location_id.id).qty_available
                        if qty < record.product_qty:
                            raise ValidationError (_('Không đủ hàng để trả. Chỉ có %s sản phẩm %s trong %s.' % (
                                qty, record.product_id.display_name, location_id.display_name)))
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
