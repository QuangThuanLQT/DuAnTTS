# -*- coding: utf-8 -*-
import logging
from odoo import api, models, fields, tools, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class sale_order_inhr(models.Model):
    _inherit = 'sale.order'

    order_from_website = fields.Boolean(default=False)
    so_state = fields.Selection(
        [('draft', 'Đặt hàng thành công'),
         ('sale', 'Đã xác nhận đơn hàng'),
         ('packing', 'Xuất kho, đóng hàng'),
         ('delivering', 'Đang giao hàng'),
         ('delivered', 'Giao hàng thành công'),
         ('cancel', 'Đã hủy')
         ], string='Trạng thái đơn hàng', compute='get_state')
    product_tmpl_web = fields.Many2many('product.template', compute='get_product_tmpl_web')
    product_order_line = fields.One2many('sale.product.template.order', 'order_id')

    @api.multi
    def _check_quotaion_in_website(self):
        order_ids = self.env['sale.order'].search([('state', '=', 'draft'), ('order_from_website', '=', True)])
        for order_id in order_ids:
            now = datetime.datetime.now()
            date_order = datetime.datetime.strptime(order_id.date_order, DEFAULT_SERVER_DATETIME_FORMAT)
            duration = (now - date_order).seconds
            if duration >= 45 * 60:
                pass

    def get_address_partner(self, obj):
        address = ''
        if obj.street:
            address += obj.street + ", "
        if obj.feosco_ward_id:
            address += obj.feosco_ward_id.name + ", "
        if obj.feosco_district_id:
            address += obj.feosco_district_id.name + ", "
        if obj.feosco_city_id:
            address += obj.feosco_city_id.name + ", "
        return address

    def get_address_transporter(self, obj):
        address = ''
        if obj.address:
            address += obj.address + ", "
        if obj.phuong_xa:
            address += obj.phuong_xa.name + ", "
        if obj.feosco_district_id:
            address += obj.feosco_district_id.name + ", "
        if obj.feosco_city_id:
            address += obj.feosco_city_id.name
        return address

    def get_state(self):
        for record in self:
            order_state_ids = sorted(record.order_state_ids, key=lambda line: line.date, reverse=True)
            if order_state_ids:
                state = order_state_ids[0].order_state
                record.so_state = state

    @api.multi
    def get_product_tmpl_web(self):
        for record in self:
            product_tmpl_ids = record.order_line.mapped('product_id').mapped('product_tmpl_id')
            if product_tmpl_ids:
                record.product_tmpl_web = product_tmpl_ids

    @api.multi
    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        if line_id:
            line_id_order = self.env['sale.order.line'].search([('id', '=', line_id)])
            if line_id_order and not line_id_order.order_id:
                for record in self:
                    line_id_order.order_id = record
        res = super(sale_order_inhr, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)
        if self._context.get('product_zero', False):
            line_id = self.env['sale.order.line'].search([('id', '=', res.get('line_id', False))])
            if line_id:
                line_id.write({
                    'order_id': False,
                    'product_uom_qty': 0
                })
        for record in self:
            for product_tmpl_order in record.product_order_line:
                if len(product_tmpl_order.order_line) == 0:
                    product_tmpl_order.unlink()
            record.button_dummy()

        return res

    @api.multi
    def _cart_delete(self, line_id, **kwargs):
        """ Add or set product quantity, add_qty can be negative """
        self.ensure_one()
        SaleOrderLineSudo = self.env['sale.product.template.order'].sudo()
        product_template_order_id = SaleOrderLineSudo.browse(line_id)
        product_template_order_id.order_line.unlink()
        product_template_order_id.unlink()

        return {}

    @api.multi
    def _cart_update_quantity(self, product_id=None, line_id=None, set_qty=0, **kwargs):
        self.ensure_one()
        SaleOrderLineSudo = self.env['sale.order.line'].sudo()
        line_id_order = SaleOrderLineSudo.search([('id', '=', line_id)])
        if line_id_order:
            line_id_order.write({
                'order_id': False,
                'product_uom_qty': set_qty
            })
        return {'line_id': line_id_order.id, 'quantity': set_qty}

class Website(models.Model):
    _inherit = 'website'

    website_user = fields.Boolean(compute='_compute_website_user')

    def _compute_website_user(self):
        for rec in self:
            rec.website_user = not (rec.env.user.has_group('tts_modifier_access_right.group_khach_hang'))

    @api.multi
    def _prepare_sale_order_values(self, partner, pricelist):
        values = super(Website, self)._prepare_sale_order_values(partner, pricelist)
        values['order_from_website'] = True
        return values

    def sale_product_domain(self):
        res = super(Website, self).sale_product_domain()
        res.append(('website_published', '=', True))
        return res