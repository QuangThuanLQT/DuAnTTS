# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class sale_order_state(models.Model):
    _name = 'sale.order.state'

    sale_id = fields.Many2one('sale.order')
    order_state = fields.Selection(
        [('draft', 'Đặt hàng thành công'),
         ('sale', 'Đã xác nhận đơn hàng'),
         ('packing', 'Xuất kho, đóng hàng'),
         ('delivering', 'Đang giao hàng'),
         ('delivered', 'Giao hàng thành công'),
         ('cancel', 'Đã hủy')
         ], string='Trạng thái đơn hàng')
    date = fields.Datetime()


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    product_uom_qty = fields.Float(digits=(16, 0))

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if self.order_id.state != 'sale':
            if not self.product_id:
                return {'domain': {'product_uom': []}}

            vals = {}
            domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
            if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
                vals['product_uom'] = self.product_id.uom_id
                vals['product_uom_qty'] = 1.0

            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=vals.get('product_uom_qty') or self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id
            )

            result = {'domain': domain}

            title = False
            message = False
            warning = {}
            if product.sale_line_warn != 'no-message':
                title = _("Warning for %s") % product.name
                message = product.sale_line_warn_msg
                warning['title'] = title
                warning['message'] = message
                result = {'warning': warning}
                if product.sale_line_warn == 'block':
                    self.product_id = False
                    return result

            name = product.name
            if product.description_sale:
                name += '\n' + product.description_sale
            vals['name'] = name
            vals['brand_name'] = product.brand_name
            vals['group_sale_id'] = product.group_sale_id and product.group_sale_id.id

            for record in self:
                if record.order_id.tax_id and record.order_id.tax_id.id:
                    record.tax_id = record.order_id.tax_id
                    record.tax_sub = int(record.order_id.tax_id.amount)

            self._compute_tax_id()

            if self.order_id.pricelist_id and self.order_id.partner_id and not self.sale_order_return:
                price_unit = self.env['account.tax']._fix_tax_included_price_company(
                    self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
                vals['price_unit'] = price_unit
            self.update(vals)

            self.onchange_product_for_ck()
            return result
        else:
            self.name = self.product_id.name
            if self.product_id.description_sale:
                self.name += '\n' + self.product_id.description_sale

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),
                                                                                 product.taxes_id, self.tax_id,
                                                                                 self.company_id)
            if not self.sale_order_return:
                self.price_unit = price_unit
                if self.order_partner_id:
                    self.onchange_product_for_ck(self.order_partner_id.id)

    @api.model
    def create(self,val):
        self.env['ir.sequence'].next_by_code('tao.lao')
        res = super(sale_order_line, self).create(val)
        return res

    @api.multi
    def write(self,val):
        if 'product_id' in val or 'product_uom_qty' in val:
            self.env['ir.sequence'].next_by_code('tao.lao')
        res = super(sale_order_line, self).write(val)
        return res

    @api.multi
    def _action_procurement_create(self):
        for record in self:
            if record.order_id and record.order_id.state == 'sale' and not record.order_id.picking_ids:
                raise UserError(_('Không thể Edit đơn hàng chưa tạo phiếu giao hàng'))
            else:
                return super(sale_order_line, self)._action_procurement_create()

    @api.constrains('product_id', 'product_uom_qty')
    def _product_id_qty_for_quotation(self):
        for record in self:
            if record.order_id.state in ['draft', 'sent']:
                if record.product_id and not record.order_id.sale_order_return:
                    if record.product_uom_qty > (record.product_id.sp_co_the_ban + record.product_uom_qty):
                        raise ValidationError(
                            _('Bạn định bán %s sản phẩm %s nhưng chỉ có %s sản phẩm có thể đặt hàng!' % (
                                record.product_uom_qty, record.product_id.display_name,
                                record.product_id.sp_co_the_ban + record.product_uom_qty)))
            else:
                if record.product_id and not record.order_id.sale_order_return:
                    dest_location = self.env.ref('stock.stock_location_customers')
                    value = sum(self.env['stock.move'].search([('product_id', '=', record.product_id.id),
                                                               ('location_dest_id', '=', dest_location.id or False), (
                                                               'group_id', '=',record.order_id.procurement_group_id.id),
                                                               ('state', 'not in', ['done', 'cancel'])]).mapped('product_uom_qty'))
                    if record.product_uom_qty > (record.product_id.sp_co_the_ban + value):
                        raise ValidationError(
                            _('Bạn định bán %s sản phẩm %s nhưng chỉ có %s sản phẩm có thể đặt hàng!' % (
                                record.product_uom_qty, record.product_id.display_name,
                                record.product_id.sp_co_the_ban)))

                        # @api.multi
                        # def write(self, val):
                        #     res = super(sale_order_line, self).write(val)
                        #     for rec in self:
                        #         if val.get('product_uom_qty', False) or val.get('product_id', False):
                        #             if (rec.product_id.qty_available - rec.product_id.sp_ban_chua_giao) < rec.product_uom_qty:
                        #                 raise ValidationError(
                        #                     _('Bạn định bán %s sản phẩm %s nhưng chỉ có %s sản phẩm có thể đặt hàng!' % (
                        #                         rec.product_uom_qty, rec.product_id.display_name,
                        #                         rec.product_id.qty_available - rec.product_id.sp_ban_chua_giao)))
                        #     return res
