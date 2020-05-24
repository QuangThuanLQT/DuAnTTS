# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import StringIO
import xlsxwriter
import logging
from lxml import etree
from datetime import datetime
import pytz
import base64
from xlrd import open_workbook
# from odoo.exceptions import UserError, ValidationError
import json
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class tts_modifier_sale(models.Model):
    _inherit = 'sale.order'

    payment_method = fields.Many2one('account.journal', string="Hình thức thanh toán",
                                     domain=[('type', 'in', ['cash', 'bank'])], required=0)
    delivery_method = fields.Selection(
        [('warehouse', 'Tới kho lấy hàng'),
         ('delivery', 'Giao tới tận nơi'),
         ('transport', 'Giao tới nhà xe'), ], string='Phương thức giao hàng', required=True, default='warehouse',
        states={'sale': [('readonly', False)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    transport_route_id = fields.Many2one('tts.transporter.route', string='Tuyến xe')
    # transport_route_ids = fields.Char()
    payment_address = fields.Char('Địa chỉ giao hàng', required=0)
    delivery_scope_id = fields.Many2one('tts.delivery.scope', string='Phạm vi giao hàng', required=0)
    delivery_scope_id_sub = fields.Many2one('tts.delivery.scope', string='Phạm vi giao hàng',
                                            related="delivery_scope_id")
    delivery_amount = fields.Monetary(string="Phụ phí giao hàng", store=True, readonly=True,
                                      compute='_delivery_amount')
    transport_amount = fields.Monetary(string="Trả trước phí ship nhà xe", store=True)
    ship_type_check = fields.Boolean(compute='_ship_type_check')
    trang_thai_dh = fields.Selection([
        ('wait_pick', 'Chờ Lấy Hàng'), ('ready_pick', 'Sẵn Sàng Lấy Hàng'), ('pick', 'Đang Lấy Hàng'),
        ('wait_pack', 'Chờ Lấy Đóng Gói'), ('pack', 'Đang Đóng Gói'),
        ('wait_out', 'Chờ Xuất Kho'), ('out', 'Đang Giao Hàngy'),
        ('done', 'Done'),
    ], string='Trạng thái đơn hàng', compute='_get_trang_thai_dh', store=False)
    confirm_user_id = fields.Many2one('res.users', string='Confirm Person', copy=False, readonly=True)
    order_state = fields.Selection(
        [('draft', 'Đặt hàng thành công'),
         ('sale', 'Đã xác nhận đơn hàng'),
         ('packing', 'Xuất kho, đóng hàng'),
         ('delivering', 'Đang giao hàng'),
         ('delivered', 'Giao hàng thành công'),
         ('cancel', 'Đã hủy')
         ], string='Trạng thái đơn hàng', default='draft')
    order_state_ids = fields.One2many('sale.order.state', 'sale_id')
    file_name = fields.Char('File Name')
    product_line_id = fields.Char(string='Product')
    city = fields.Char(compute='get_city_partner', store=True)

    @api.depends('partner_id.feosco_city_id')
    def get_city_partner(self):
        for rec in self:
            city = rec.partner_id.feosco_city_id
            rec.city = city.name

    @api.model
    def get_city_list(self):
        city_ids = self.env['sale.order'].search([]).with_context({'lang': self.env.user.lang or 'vi_VN'}).mapped(
            'city')
        city_list = []
        for city_id in city_ids:
            if city_id not in city_list:
                city_list.append(city_id)
        return city_list

    @api.model
    def get_search_city(self, city_name):
        if city_name:
            city = self.search([('city', '=', city_name)])
            return city.ids

    @api.model
    def get_product_name_report(self, product_id):
        variants = [product_id.name]
        for attr in product_id.attribute_value_ids:
            if attr.attribute_id.name in ('Size', 'size'):
                variants.append(('Size ' + attr.name))
            else:
                variants.append((attr.name))

        product_name = ' - '.join(variants)
        return product_name

    @api.multi
    def update_sale_order(self):
        for rec in self:
            for line in rec.order_line:
                line.product_id_change()
                line.product_uom_change()
            rec.button_dummy()

    @api.multi
    def action_quotation_send(self):
        if not self.order_line:
            pass
        else:
            return super(tts_modifier_sale, self).action_quotation_send()

    @api.multi
    def onchange_order_line(self):
        for order in self:
            line_data = {}
            promotion_data = {}
            for line in order.order_line:
                if line.product_id:
                    line_data.update({
                        str(line.product_id.product_tmpl_id): line_data.get(str(line.product_id.product_tmpl_id),
                                                                            0) + line.product_uom_qty
                    })
            if line_data:
                template_list = order.order_line.mapped('product_id.product_tmpl_id')
                for template in template_list:
                    qty_tem = line_data.get(str(template), False)
                    now = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    pricelist = self.env['product.pricelist.line'].search([
                        ('line_id', '=', template.id),
                        ('start_date', '<=', now),
                        ('end_date', '>=', now),
                        ('quantity_min', '<=', qty_tem)
                    ], order='quantity_min DESC', limit=1)
                    if pricelist:
                        promotion_data.update({
                            str(template): pricelist.giam_gia
                        })
                        # else:
                        #     del line_data[str(template)]
            for line in order.order_line:
                pricelist_tem = promotion_data.get(str(line.product_id.product_tmpl_id), False)
                if pricelist_tem:
                    line.price_unit = line.product_id.lst_price - pricelist_tem
                else:
                    line.price_unit = line.product_id.lst_price

    @api.multi
    def get_queue_server(self):
        queue_server = self.env['setting.queue.server'].search([('active', '=', True)], limit=1)
        if queue_server:
            return queue_server
        else:
            return False

    @api.multi
    def so_create_queue_client(self):
        import json
        import gearman

        queue_server = self.get_queue_server()
        if queue_server:
            self._cr.commit()
            gm_client = gearman.GearmanClient([queue_server.queue_server])
            for rec in self:
                values = json.dumps({
                    'sale_id': rec.id
                })
                job_name = '%s_sale_order_create_picking' % (queue_server.prefix,)
                gm_client.submit_job(job_name.encode('ascii', 'ignore'), values, priority=gearman.PRIORITY_HIGH,
                                     background=True)

    def _generation_move_line_tts(self, line, picking_id, picking_type_id, procurement_id, move_line=False):
        location_id, location_dest_id = self._get_picking_location(picking_type_id)
        data = {
            'product_id': line.product_id.id,
            'product_uom_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'location_id': location_id,
            'picking_type_id': picking_type_id.id,
            'warehouse_id': picking_type_id.warehouse_id.id,
            'location_dest_id': location_dest_id,
            'name': ' ',
            'procure_method': 'make_to_stock',
            'origin': self.name,
            'price_unit': line.price_unit * (1 - (line.discount or 0.0) / 100.0) or 0,
            'date': self.date_order,
            'group_id': line.order_id.procurement_group_id.id,
            'procurement_id': procurement_id.id,
            'rule_id': procurement_id.rule_id.id,
            'picking_id': picking_id.id,
            'partner_id': self.partner_id.id,
        }
        if move_line:
            data.update(({
                'move_dest_id': move_line.id,
            }))
        return self.env['stock.move'].create(data)

    def _get_picking_location(self, picking_type_id):
        procurement_rule = self.env['procurement.rule'].search([('picking_type_id', '=', picking_type_id.id)],
                                                               limit=1)
        location_id = procurement_rule.location_src_id
        location_dest_id = procurement_rule.location_id
        return location_id.id, location_dest_id.id

    def _get_picking_value_tts(self, picking_type_id):

        location_id, location_dest_id = self._get_picking_location(picking_type_id)
        picking_id = self.env['stock.picking'].create({
            'picking_type_id': picking_type_id.id,
            'partner_id': self.partner_id.id,
            'origin': self.name,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'check_return_picking': False,
            'min_date': self.date_order,
            'picking_note': self.note
        })

        return picking_id

    @api.multi
    def create_picking_tts(self):
        for rec in self:
            if not rec.picking_ids and rec.state == 'sale':
                if not rec.procurement_group_id:
                    vals = rec._prepare_procurement_group()
                    rec.procurement_group_id = self.env["procurement.group"].create(vals)

                warehouse_id = self.warehouse_id
                out_type_id = warehouse_id.out_type_id
                pack_type_id = warehouse_id.pack_type_id
                pick_type_id = warehouse_id.pick_type_id

                # create delivery
                delivery_id = self._get_picking_value_tts(out_type_id)
                delivery_id.write({
                    'state_delivery': 'waiting_another_operation',
                })

                # create pack
                pack_id = self._get_picking_value_tts(pack_type_id)
                pack_id.write({
                    'state_pack': 'waiting_another_operation',
                })

                # create pick
                pick_id = self._get_picking_value_tts(pick_type_id)
                check = False
                if self.payment_method.type == 'cash':
                    check = True
                elif self.payment_method.type == 'bank' and self.trang_thai_tt == 'tt_1_phan' and self.delivery_method in (
                        'delivery', 'warehouse'):
                    check = True
                elif self.payment_method.type == 'bank' and self.trang_thai_tt == 'done_tt':
                    check = True
                if check:
                    pick_id.write({
                        'state_pick': 'waiting_pick',
                    })
                    state_pick = 'ready_pick'
                    rec.trang_thai_dh = 'ready_pick'
                else:
                    state_pick = 'waiting_pick'
                    rec.trang_thai_dh = 'waiting_pick'
                pick_id.write({
                    'state_pick': state_pick,
                })

                delivery_line_ids = self.env['stock.move']
                pack_line_ids = self.env['stock.move']
                pick_line_ids = self.env['stock.move']
                index = 0
                total = len(rec.order_line.ids)
                for line in rec.order_line:
                    index += 1
                    vals = line._prepare_order_line_procurement(group_id=line.order_id.procurement_group_id.id)
                    vals['product_qty'] = line.product_uom_qty
                    new_proc = self.env["procurement.order"].with_context(procurement_autorun_defer=True).create(vals)
                    new_proc._assign()

                    # create move delivery
                    _logger.info("%s/%s----------------------------------%s" % (index, total, str(datetime.now()),))
                    _logger.info("+" + str(datetime.now()))
                    delivery_line_id = self._generation_move_line_tts(line, delivery_id, out_type_id, new_proc)
                    delivery_line_ids += delivery_line_id
                    _logger.info("Create delivery" + str(datetime.now()))

                    # create move pack
                    _logger.info("+" + str(datetime.now()))
                    pack_line_id = self._generation_move_line_tts(line, pack_id, pack_type_id, new_proc,
                                                                  delivery_line_id)
                    pack_line_ids += pack_line_id
                    _logger.info("Create move pack" + str(datetime.now()))

                    # create move pick
                    _logger.info("+" + str(datetime.now()))
                    pick_line_id = self._generation_move_line_tts(line, pick_id, pick_type_id, new_proc, pack_line_id)
                    pick_line_ids += pick_line_id
                    _logger.info("Create move pick" + str(datetime.now()))

                delivery_id.action_confirm()
                pack_id.action_confirm()
                pick_id.action_confirm()
                pick_id.action_assign()

                if rec.state != 'sale':
                    pick_id.action_cancel()
                    pick_id.state_pick = 'cancel'
                    pack_id.action_cancel()
                    pack_id.state_pack = 'cancel'
                    delivery_id.action_cancel()
                    delivery_id.state_delivery = 'cancel'
                rec.queue_procurement = False
                return True

    @api.multi
    def create_so_picking_from_queue(self):
        for rec in self:
            if not rec.picking_ids.filtered(lambda p: p.state != 'cancel'):
                rec.order_line.mapped('procurement_ids').filtered(lambda p: p.state != 'cancel').unlink()
                rec.queue_procurement = False
                rec.create_picking_tts()
        return True

    @api.multi
    def multi_create_picking(self):
        ids = self.env.context.get('active_ids', [])
        sale_order_ids = self.browse(ids)
        for sale_order_id in sale_order_ids:
            if not sale_order_id.picking_ids.filtered(lambda p: p.state != 'cancel'):
                sale_order_id.order_line.mapped('procurement_ids').filtered(lambda p: p.state != 'cancel').unlink()
                sale_order_id.create_picking_tts()

    @api.multi
    def action_confirm_order(self):
        if not self.order_line:
            pass
        else:
            if self.state not in ['draft', 'sent']:
                return None
            res = super(tts_modifier_sale, self).action_confirm_order()
            for order in self:
                for line in self.order_line:
                    if (line.product_id.sp_co_the_ban + line.product_uom_qty) < line.product_uom_qty:
                        raise ValidationError(
                            _('Bạn định bán %s sản phẩm %s nhưng chỉ có %s sản phẩm có thể đặt hàng!' % (
                                line.product_uom_qty, line.product_id.display_name,
                                line.product_id.sp_co_the_ban + line.product_uom_qty)))
                order.confirm_user_id = self.env.uid

                # order_state_id = self.env['sale.order.state'].create({
                #     'sale_id': order.id,
                #     'order_state': 'sale',
                #     'date': datetime.now()
                # })
            self.env.cr.commit()
            self.so_create_queue_client()
            return res

    @api.model
    def _cron_queue_create_picking(self):
        sales = self.search([
            ('queue_procurement', '=', True),
            ('state', '=', 'sale'),
        ])

        if len(sales) > 0:
            for sale in sales:
                if sale.queue_procurement:
                    sale.create_picking_tts()

            sales.write({
                'queue_procurement': False
            })

        return True

    @api.multi
    def action_confirm(self):
        res = super(tts_modifier_sale, self).action_confirm()
        for record in self:
            record.order_state = 'sale'
            order_state_id = self.env['sale.order.state'].create({
                'sale_id': record.id,
                'order_state': 'sale',
                'date': datetime.now()
            })
        return res

    @api.depends('picking_ids')
    def _get_trang_thai_dh(self):
        for rec in self:
            if rec.picking_ids:
                if all(picking.state != 'done' for picking in
                       rec.picking_ids.filtered(lambda line: line.check_is_pick == True)):
                    rec.trang_thai_dh = 'pick'
                elif all(picking.state != 'done' for picking in
                         rec.picking_ids.filtered(lambda line: line.check_is_pack == True)):
                    rec.trang_thai_dh = 'pack'
                else:
                    rec.trang_thai_dh = 'out'

    @api.model
    def search_trang_thai_dh(self, state):
        sale_ids = self.search([]).filtered(lambda s: s.trang_thai_dh == state)
        return sale_ids.ids

    @api.depends('delivery_method', 'transport_route_id')
    def _ship_type_check(self):
        for record in self:
            if record.delivery_method == 'transport':
                if record.transport_route_id and record.transport_route_id.transporter_id:
                    if record.transport_route_id.transporter_id.ship_type == 'tra_truoc':
                        record.ship_type_check = True

    @api.depends('order_line.price_total', 'delivery_method', 'delivery_scope_id', 'transport_route_id')
    def _delivery_amount(self):
        for order in self:
            cs_free_delivery = self.env['ir.values'].get_default('sale.config.settings', 'cs_free_delivery')
            delivery_amount = 0

            amount_untaxed = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
            if amount_untaxed < cs_free_delivery:
                # “Giao tới tận nơi”: Giá trị “Tỉnh/TP >> Quận/Huyện >> Phường/Xã” trong địa chỉ khách hàng trùng với
                # giá trị “Tỉnh/TP >> Quận/Huyện >> Phường/Xã” của phạm vi giao hàng nào thì “Phụ phí giao hàng” = “Phí giao hàng phát sinh” của phạm vi giao hàng đó.
                if order.delivery_method == 'delivery' and order.delivery_scope_id:
                    delivery_scope_id = self.env['tts.delivery.scope'].sudo().search(
                        [('feosco_city_id', '=', order.partner_id.feosco_city_id.id or False),
                         ('feosco_district_id', '=', order.partner_id.feosco_district_id.id or False),
                         ('phuong_xa', '=', order.partner_id.feosco_ward_id.id or False)], limit=1)
                    if delivery_scope_id:
                        delivery_amount = delivery_scope_id.phi_giao_hang
                    else:
                        delivery_amount = order.delivery_scope_id.phi_giao_hang or 0

                # “Tới kho lấy hàng”: Phụ phí giao hàng = 0
                elif order.delivery_method == 'warehouse':
                    delivery_amount = 0

                # “Giao tới nhà xe”:  Giá trị “Đi từ Tỉnh/TP >> Đi từ Quận/Huyện >> Đi từ Phường/Xã”  trong cấu hình nhà xe trùng với giá trị “Tỉnh/TP >> Quận/Huyện >> Phường/Xã”
                # của phạm vi giao hàng nào thì “Phụ phí giao hành” = “Phí giao hàng phát sinh” của phạm vi giao hàng đó
                elif order.delivery_method == 'transport':
                    transport_id = self.env['tts.delivery.scope'].sudo().search(
                        [('feosco_city_id', '=', order.transport_route_id.feosco_city_id.id or False),
                         ('feosco_district_id', '=', order.transport_route_id.feosco_district_id.id or False),
                         ('phuong_xa', '=', order.transport_route_id.phuong_xa.id or False)])
                    if transport_id:
                        delivery_amount = transport_id.phi_giao_hang
                    else:
                        delivery_amount = order.delivery_scope_id.phi_giao_hang or 0
            order.update({
                'delivery_amount': delivery_amount,
            })

    @api.multi
    def button_dummy(self):
        self.onchange_order_line()
        res = super(tts_modifier_sale, self).button_dummy()
        for order in self:
            transport_amount = 0
            delivery_amount = order.delivery_amount
            amount_total = order.amount_total
            if order.delivery_method == 'transport' and order.ship_type_check == True:
                transport_amount = order.transport_amount
            order.update({
                'amount_total': amount_total + transport_amount + delivery_amount
            })
        return res

    @api.onchange('partner_id')
    def onchange_paartner_delivery(self):
        if self.partner_id and not self.sale_order_return:
            self.delivery_method = self.partner_id.delivery_method
            self.transport_route_id = self.partner_id.transport_route_id
            self.payment_method = self.partner_id.payment_method
            # transport_route_ids = self.env['tts.transporter.route'].search([
            #     ('feosco_city_id', '=', self.partner_id.feosco_city_id.id),
            #     ('feosco_district_id', '=', self.partner_id.feosco_district_id.id),
            # ])
            # if transport_route_ids:
            #     self.transport_route_ids = transport_route_ids.ids

    @api.onchange('delivery_method', 'partner_id')
    def onchange_delivery_method(self):
        if self.delivery_method == 'delivery':
            self.payment_address = "%s, %s, %s, %s" % (
                self.partner_id.street or '', self.partner_id.feosco_ward_id.name or '',
                self.partner_id.feosco_district_id.name or '',
                self.partner_id.feosco_city_id.name or '')
            delivery_scope_ids = self.env['tts.delivery.scope'].search(
                [('feosco_city_id', '=', self.partner_id.feosco_city_id.id),
                 ('feosco_district_id', '=', self.partner_id.feosco_district_id.id),
                 ('phuong_xa', '=', self.partner_id.feosco_ward_id.id)])
            if delivery_scope_ids:
                self.delivery_scope_id = delivery_scope_ids[0]
            return {'domain': {'delivery_scope_id': [('id', 'in', delivery_scope_ids.ids)]}}

        elif self.delivery_method == 'transport':
            transport_route_ids = self.env['tts.transporter.route'].search([
                ('feosco_city_id', '=', self.partner_id.feosco_city_id.id),
                ('feosco_district_id', '=', self.partner_id.feosco_district_id.id),
            ])
            if transport_route_ids:
                if self.partner_id.transport_route_id:
                    self.transport_route_id = self.partner_id.transport_route_id
                else:
                    self.transport_route_id = transport_route_ids[0]
                self.payment_address = "%s, %s, %s, %s" % (
                    self.transport_route_id.transporter_id.address or '',
                    self.transport_route_id.transporter_id.phuong_xa.name or '',
                    self.transport_route_id.transporter_id.feosco_district_id.name or '',
                    self.transport_route_id.transporter_id.feosco_city_id.name or '')
            else:
                self.transport_route_id = None
            return {'domain': {'transport_route_id': [('id', 'in', transport_route_ids.ids)]}}

    @api.onchange('delivery_method', 'transport_route_id')
    def onchange_get_delivery_scope(self):
        if self.delivery_method == 'delivery':
            delivery_scope_ids = self.env['tts.delivery.scope'].search(
                [('feosco_city_id', '=', self.partner_id.feosco_city_id.id),
                 ('feosco_district_id', '=', self.partner_id.feosco_district_id.id),
                 ('phuong_xa', '=', self.partner_id.feosco_ward_id.id)])
            if delivery_scope_ids:
                self.delivery_scope_id = delivery_scope_ids[0]
            return {'domain': {'delivery_scope_id': [('id', 'in', delivery_scope_ids.ids)]}}
        elif self.delivery_method == 'transport':
            delivery_scope_ids = self.env['tts.delivery.scope']
            if self.transport_route_id:
                delivery_scope_ids = self.env['tts.delivery.scope'].search(
                    [('feosco_city_id', '=', self.transport_route_id.transporter_id.feosco_city_id.id),
                     ('feosco_district_id', '=', self.transport_route_id.transporter_id.feosco_district_id.id),
                     ('phuong_xa', '=', self.transport_route_id.transporter_id.phuong_xa.id)])
                if delivery_scope_ids:
                    self.delivery_scope_id = delivery_scope_ids[0]
            return {'domain': {'delivery_scope_id': [('id', 'in', delivery_scope_ids.ids)]}}

    @api.onchange('transport_route_id')
    def onchange_transport_route_id(self):
        if self.transport_route_id:
            self.payment_address = "%s, %s, %s, %s" % (
                self.transport_route_id.transporter_id.address or '',
                self.transport_route_id.transporter_id.phuong_xa.name or '',
                self.transport_route_id.transporter_id.feosco_district_id.name or '',
                self.transport_route_id.transporter_id.feosco_city_id.name or '')

    @api.model
    def create(self, vals):
        if "order_line" in vals.keys():
            product_list = []
            for obj in vals['order_line']:
                if obj[2]['product_id'] not in product_list:
                    product_list.append(obj[2]['product_id'])
            list_new = vals['order_line']
            new_list = []
            for obj in product_list:
                count = 0
                qty = 0
                for element in list_new:
                    if obj == element[2]['product_id']:
                        qty += element[2]['product_uom_qty']
                for ele in list_new:
                    if obj == ele[2]['product_id']:
                        count += 1
                        if count == 1:
                            ele[2]['product_uom_qty'] = qty
                            new_list.append(ele)
            vals['order_line'] = new_list
        res = super(tts_modifier_sale, self.with_context(mail_create_nosubscribe=True)).create(vals)
        res.confirmation_date = datetime.now()
        order_state_id = self.env['sale.order.state'].create({
            'sale_id': res.id,
            'order_state': 'draft',
            'date': datetime.now()
        })
        return res

    @api.multi
    def write(self, vals):
        product_list_ext = []
        product_list_new = []
        for record in self:
            if 'order_line' in vals and record.trang_thai_dh in ('done', 'delivery'):
                raise UserError(_('Không thể Edit đơn hàng ở trạng thái Delivery hoặc Done'))
        if "order_line" in vals.keys():
            new_list = vals['order_line']
            pro_list = []
            for att in new_list:
                if att[0] == 4:
                    s = self.order_line.browse(att[1])
                    if s.product_id and s.product_id.id not in product_list_ext:
                        product_list_ext.append(s.product_id.id)
                if att[0] == 1:
                    s = self.order_line.browse(att[1])
                    if s.product_id and s.product_id.id not in product_list_ext:
                        product_list_ext.append(s.product_id.id)
                if att[0] == 0:
                    if att[2]['product_id'] not in product_list_new:
                        product_list_new.append(att[2]['product_id'])
            if not product_list_ext and self.order_line:
                for line in self.order_line:
                    if line.product_id.id and line.product_id.id not in product_list_ext:
                        product_list_ext.append(line.product_id.id)
            for obj in product_list_new:
                pro_qty = 0
                if obj in product_list_ext:
                    for att in new_list:
                        if att[0] == 4:
                            o = self.order_line.browse(att[1])
                            if o.product_id.id == obj:
                                pro_qty += o.product_uom_qty
                        if att[0] == 1:
                            o = self.order_line.browse(att[1])
                            if o.product_id.id == obj:
                                pro_qty += att[2].get('product_uom_qty', False) or 1
                        if att[1] == 0:
                            if att[2] and att[2]['product_id'] == obj:
                                pro_qty += att[2].get('product_uom_qty', False) or 1
                                if self.order_line:
                                    for line in self.order_line:
                                        if (line.product_id and line.product_id.id == obj) and att[2].get(
                                                'product_uom_qty') == None:
                                            pro_qty += line.product_uom_qty

                    for att1 in new_list:
                        if att1[0] == 4:
                            o = self.order_line.browse(att1[1])
                            if o.product_id.id == obj:
                                o.product_uom_qty = pro_qty
                                # o.product_uos_qty = pro_qty
                        if att1[0] == 1:
                            o = self.order_line.browse(att1[1])
                            if o.product_id.id == obj:
                                att1[2]['product_uom_qty'] = pro_qty
                                o.product_uom_qty = pro_qty
                        if att1[0] == 0 and self:
                            for line in self.order_line:
                                if line.product_id and line.product_id.id == obj:
                                    line.product_uom_qty = pro_qty
                                    # line.product_uos_qty = pro_qty
            for obj1 in product_list_new:
                pro_qty = 0
                count = 0
                if obj1 not in product_list_ext:
                    for att1 in new_list:
                        if att1[0] == 0:
                            if att1[2]['product_id'] == obj1:
                                pro_qty += att1[2].get('product_uom_qty') if 'product_uom_qty' in att1[2] else 1
                    for att2 in new_list:
                        if att2[0] == 0:
                            if att2[2]['product_id'] == obj1:
                                count += 1
                                if count == 1:
                                    att2[2]['product_uom_qty'] = pro_qty
                                    pro_list.append(att2)

            for obj2 in product_list_ext:
                if obj2 not in product_list_new:
                    for att2 in new_list:
                        if att2[0] == 4:
                            o = self.order_line.browse(att2[1])
                            if o.product_id.id == obj2:
                                pro_list.append(att2)
            for att3 in new_list:
                if att3[0] == 2:
                    pro_list.append(att3)
                if att3[0] == 1:
                    check = False
                    if att3[2].get('product_id', False):
                        for line in pro_list:
                            o = self.order_line.browse(line[1])
                            if o.product_id.id == att3[2].get('product_id'):
                                o.product_uom_qty += att3[2].get('product_uom_qty') or self.order_line.browse(
                                    att3[1]).product_uom_qty
                                new_line = att3
                                new_line[0] = 2
                                pro_list.append(new_line)
                                check = True
                    if not check:
                        pro_list.append(att3)

            vals['order_line'] = pro_list
        res = super(tts_modifier_sale, self).write(vals)
        if vals.get('delivery_method', False):
            for rec in self:
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                if 'alpha' in base_url:
                    feosco_city_id = self.env['feosco.city'].search([('name', '=', 'Hồ Chí Minh')], limit=1)
                else:
                    feosco_city_id = self.env['feosco.city'].search([('name', '=', 'Đà Nẵng')], limit=1)
                income_ids = self.env['income.inventory'].sudo().search([('source_sale_id', '=', rec.id)])
                if rec.delivery_method == 'warehouse':
                    income_ids.write({
                        'delivery_method': vals.get('delivery_method', False),
                        'city_id': feosco_city_id.id,
                        'district_id': '',
                        'ward_id': '',
                    })
                elif rec.delivery_method == 'delivery':
                    income_ids.write({
                        'delivery_method': vals.get('delivery_method', False),
                        'city_id': rec.partner_id.feosco_city_id.id,
                        'district_id': rec.partner_id.feosco_district_id.id,
                        'ward_id': rec.partner_id.feosco_ward_id.id,
                    })
                elif rec.delivery_method == 'transport':
                    income_ids.write({
                        'delivery_method': vals.get('delivery_method', False),
                        'city_id': rec.transport_route_id.transporter_id.feosco_city_id.id,
                        'district_id': rec.transport_route_id.transporter_id.feosco_district_id.id,
                        'ward_id': rec.transport_route_id.transporter_id.phuong_xa.id,
                    })
        if not 'button_dummy_create' in self._context and not 'button_dummy_write' in self._context:
            # if 'transport_amount' in vals or 'delivery_method' in vals:
            self.with_context(button_dummy_write=True).button_dummy()
        for record in self:
            if record.state == 'cancel':
                order_state_id = self.env['sale.order.state'].create({
                    'sale_id': record.id,
                    'order_state': 'cancel',
                    'date': datetime.now()
                })
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(tts_modifier_sale, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                             toolbar=toolbar, submenu=submenu)
        sale_order_id = self.env.ref('sale.action_orders')
        if self._context.get('params', False) and self._context.get('params').get('action', False) == sale_order_id.id:
            if view_type in 'tree':
                doc = etree.XML(res['arch'], parser=None, base_url=None)
                first_node = doc.xpath("//tree")[0]
                first_node.set('create', 'false')
                res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def search_operation_state(self, state):
        order_ids = self.search([('sale_order_return', '=', True)])
        ids = order_ids.filtered(lambda r: r.trang_thai_dh == state)
        return ids.ids

    @api.model
    def search_operation_state_sale_order(self, trang_thai_dh):
        order_ids = self.search([('sale_order_return', '=', False)])
        ids = order_ids.filtered(lambda r: r.trang_thai_dh == trang_thai_dh)
        return ids.ids

    def _get_datetime_utc(self, datetime_val):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(datetime_val, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime(
            '%d/%m/%Y %H:%M')
        return resuft

    @api.multi
    def import_data_excel(self):
        for record in self:
            if record.import_data:
                data = base64.b64decode(record.import_data)
                wb = open_workbook(file_contents=data)
                sheet = wb.sheet_by_index(0)

                order_line = record.order_line.browse([])
                for row_no in range(sheet.nrows):
                    if row_no > 0:
                        row = (map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(
                            row.value), sheet.row(row_no)))
                        if row[0]:
                            try:
                                default_code = str(int(float(row[0].strip())))
                            except:
                                default_code = row[0].strip()
                            product = self.env['product.product'].search([
                                '|', ('default_code', '=', default_code),
                                ('barcode', '=', default_code)
                            ], limit=1)
                            if product:
                                line_data = {
                                    'product_id': product.id,
                                    'product_uom': product.uom_id.id,
                                    'price_unit': product.lst_price,
                                    'product_uom_qty': int(float(row[1])),
                                }
                                line = record.order_line.new(line_data)
                                line.product_id_change()
                                line.product_uom_change()
                                order_line += line
                record.order_line = order_line

                # if attribute_ids in product.attribute_value_ids:
                #     True
                # if product and product.id:
                #     try:
                #         size = str(int(float(row[3].strip())))
                #     except:
                #         size = row[3].strip()
                #     attribute_ids = self.env['product.attribute.value'].search(
                #         [('name', 'in', (row[2], size))])
                #     check_attribute = True
                #     if attribute_ids:
                #         for attribute_id in attribute_ids:
                #             if attribute_id not in product.attribute_value_ids:
                #                 check_attribute = False
                #                 break
                #         if check_attribute:
                #             line_data = {
                #                 'product_id': product.id,
                #                 'product_uom': product.uom_id.id,
                #                 'price_unit': product.lst_price,
                #                 'product_uom_qty': int(float(row[4])),
                #             }
                #             # if row[2]:
                #                 # discount = float(row[2])
                #                 # line_data['discount'] = discount
                #             #     if row[3]:
                #             #         raise ValidationError(_('Không được có cả chiết khấu và giá đã chiết khấu.'))
                #             # elif row[3]:
                #             #     price_discount = float(row[3])
                #             #     line_data['price_discount'] = price_discount
                #             line = record.order_line.new(line_data)
                #             line.product_id_change()
                #             line.product_uom_change()
                #             # if not row[2] and not row[3]:
                #             #     line.onchange_product_for_ck(self.partner_id.id)
                #             order_line += line
                # record.order_line = order_line

    # Export data

    @api.multi
    def print_data_excel(self):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Export Overview')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'right', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:A', 50)
        worksheet.set_column('B:D', 15)

        summary_header = ['Product name', 'Ordered Qty', 'Unit Price', 'Subtotal']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
        # worksheet.autofilter('A1:D51')
        for record in self.order_line:
            row += 1

            worksheet.write(row, 0, record.product_id.display_name, text_style)
            worksheet.write(row, 1, record.product_uom_qty, text_style)
            worksheet.write(row, 2, record.price_unit, body_bold_color_number)
            worksheet.write(row, 3, record.price_subtotal or '', body_bold_color_number)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({
            'name': '%s.xlsx' % (self.name),
            'datas_fname': '%s.xlsx' % (self.name),
            'datas': result
        })
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(download_url)}

    @api.model
    def print_quotaion_excel(self, response):
        quotaion_ids = self.env['sale.order'].search(
            [('state', 'in', ('draft', 'sent', 'cancel')), ('sale_order_return', '=', False)])
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Export Overview')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:F', 20)

        summary_header = ['Mã báo giá', 'Thời gian đặt hàng', 'Mã khách hàng', 'Khách hàng', 'Nhân viên bán hàng',
                          'Create by', 'Ghi chú',
                          'Tổng', 'Trạng thái']
        row = 0
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for quotaion_id in quotaion_ids:
            row += 1
            state = dict(self.env['sale.order'].fields_get(allfields=['state'])['state'][
                             'selection'])
            date_order = ''
            if quotaion_id.confirmation_date:
                date_order = self._get_datetime_utc(quotaion_id.confirmation_date)
            worksheet.write(row, 0, quotaion_id.name, text_style)
            worksheet.write(row, 1, date_order, text_style)
            worksheet.write(row, 2, quotaion_id.partner_id.ref or '', text_style)
            worksheet.write(row, 3, quotaion_id.partner_id.name, text_style)
            worksheet.write(row, 4, quotaion_id.user_id.name or '', text_style)
            worksheet.write(row, 5, quotaion_id.create_uid.name or '', text_style)
            worksheet.write(row, 6, quotaion_id.note or '', text_style)
            worksheet.write(row, 7, quotaion_id.amount_total, body_bold_color_number)
            worksheet.write(row, 8, state.get(quotaion_id.state), text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.model
    def print_sale_excel(self, response, type=False):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        quotaion_ids = self.env['sale.order'].search(domain)
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Export Overview')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:K', 20)

        summary_header = ['Mã báo giá', 'Thời gian tạo', 'Thời gian xác nhận', 'Mã khách hàng', 'Khách hàng',
                          'Tỉnh/Thành phố', 'Nhân viên bán hàng', 'Created by', 'Validate by', 'Ghi chú',
                          'Hình thức thanh toán', 'Tổng', 'Số tiền còn phải thu', 'Số tiền đã thu',
                          'Trạng thái thanh toán',
                          'Trạng thái đơn hàng', 'Trạng thái hoạt động']
        summary_header_return = ['Reference Return', 'Thời gian tạo', 'Mã khách hàng', 'Khách hàng',
                                 'Nhân viên bán hàng', 'Created by', 'Validate by', 'Ghi chú',
                                 'Lý do trả hàng', 'Sale Order', 'Tổng', 'Số tiền còn phải trả', 'Số tiền đã trả',
                                 'Trạng thái thanh toán', 'Trạng thái đơn hàng', 'Trạng thái hoạt động']
        row = 0
        if not type:
            [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), body_bold_color) for
             header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
            # worksheet.autofilter('A1:K1')
            for quotaion_id in quotaion_ids:
                row += 1
                state = dict(self.env['sale.order'].fields_get(allfields=['state'])['state'][
                                 'selection'])
                tt_donhang = dict(self.env['sale.order'].fields_get(allfields=['trang_thai_dh'])['trang_thai_dh'][
                                      'selection'])
                tt_thanhtoan = dict(self.env['sale.order'].fields_get(allfields=['trang_thai_tt'])['trang_thai_tt'][
                                        'selection'])
                confirmation_date = ''
                create_date = ''
                if quotaion_id.confirmation_date:
                    confirmation_date = self._get_datetime_utc(quotaion_id.confirmation_date)
                if quotaion_id.create_date:
                    create_date = self._get_datetime_utc(quotaion_id.create_date)
                worksheet.write(row, 0, quotaion_id.name, text_style)
                worksheet.write(row, 1, create_date, text_style)
                worksheet.write(row, 2, confirmation_date, text_style)
                worksheet.write(row, 3, quotaion_id.partner_id.ref or '', text_style)
                worksheet.write(row, 4, quotaion_id.partner_id.name, text_style)
                worksheet.write(row, 5, quotaion_id.partner_id.feosco_city_id.name, text_style)
                worksheet.write(row, 6, quotaion_id.user_id.name or '', text_style)
                worksheet.write(row, 7, quotaion_id.create_uid.name or '', text_style)
                worksheet.write(row, 8, quotaion_id.confirm_user_id.name or '', text_style)
                worksheet.write(row, 9, quotaion_id.note or '', text_style)
                worksheet.write(row, 10, quotaion_id.payment_method.display_name or '', text_style)
                worksheet.write(row, 11, quotaion_id.amount_total, body_bold_color_number)
                worksheet.write(row, 12, quotaion_id.con_phai_thu, body_bold_color_number)
                worksheet.write(row, 13, quotaion_id.so_tien_da_thu, body_bold_color_number)
                worksheet.write(row, 14, tt_thanhtoan.get(quotaion_id.trang_thai_tt), text_style)
                worksheet.write(row, 15, state.get(quotaion_id.state), text_style)
                worksheet.write(row, 16, tt_donhang.get(quotaion_id.trang_thai_dh), text_style)
        elif type and type == 'return':
            [worksheet.write(row, header_cell, unicode(summary_header_return[header_cell], "utf-8"), body_bold_color)
             for
             header_cell in range(0, len(summary_header_return)) if summary_header_return[header_cell]]

            for quotaion_id in quotaion_ids:
                row += 1
                state = dict(self.env['sale.order'].fields_get(allfields=['state'])['state'][
                                 'selection'])
                tt_donhang = dict(self.env['sale.order'].fields_get(allfields=['trang_thai_dh'])['trang_thai_dh'][
                                      'selection'])
                tt_thanhtoan = dict(self.env['sale.order'].fields_get(allfields=['trang_thai_tt'])['trang_thai_tt'][
                                        'selection'])
                confirmation_date = ''
                if quotaion_id.confirmation_date:
                    confirmation_date = self._get_datetime_utc(quotaion_id.confirmation_date)
                worksheet.write(row, 0, quotaion_id.name, text_style)
                worksheet.write(row, 1, confirmation_date, text_style)
                worksheet.write(row, 2, quotaion_id.partner_id.ref or '', text_style)
                worksheet.write(row, 3, quotaion_id.partner_id.name, text_style)
                worksheet.write(row, 4, quotaion_id.user_id.name or '', text_style)
                worksheet.write(row, 5, quotaion_id.create_uid.name or '', text_style)
                worksheet.write(row, 6, quotaion_id.confirm_user_id.name or '', text_style)
                worksheet.write(row, 7, quotaion_id.note or '', text_style)
                worksheet.write(row, 8, quotaion_id.reason_cancel.name or '', text_style)
                sale_order = ', '.join([order.name for order in quotaion_id.sale_order_return_ids])
                worksheet.write(row, 9, sale_order, body_bold_color_number)
                worksheet.write(row, 10, quotaion_id.amount_total, body_bold_color_number)
                worksheet.write(row, 11, quotaion_id.con_phai_thu, body_bold_color_number)
                worksheet.write(row, 12, quotaion_id.so_tien_da_thu, body_bold_color_number)
                worksheet.write(row, 13, tt_thanhtoan.get(quotaion_id.trang_thai_tt), text_style)
                worksheet.write(row, 14, state.get(quotaion_id.state), text_style)
                worksheet.write(row, 15, tt_donhang.get(quotaion_id.trang_thai_dh), text_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.model
    def print_sale_excel_detail(self, response, type=False):
        domain = []
        if self._context.get('domain', False):
            domain = self._context.get('domain')
        quotaion_ids = self.env['sale.order'].search(domain)
        quotaion_ids_ = self.env['sale.order'].search(
            [('state', 'in', ('draft', 'sent', 'cancel')), ('sale_order_return', '=', False)])
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Export Detail')

        body_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        text_style = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number = workbook.add_format(
            {'bold': False, 'font_size': '11', 'align': 'left', 'valign': 'vcenter'})
        body_bold_color_number.set_num_format('#,##0')

        worksheet.set_column('A:N', 20)

        attribute_list = quotaion_ids.mapped('order_line').mapped('product_id').mapped('attribute_value_ids').mapped(
            'attribute_id').mapped('name')
        summary_header_quo = ['Mã báo giá', 'Ngày đặt hàng', 'Mã khách hàng', 'Khách hàng', 'SĐT Khách hàng',
                              'Nhân viên bán hàng',
                              'Created by', 'Tổng', 'Ghi chú', 'Mã biến thể nội bộ',
                              'Tên sản phẩm'] + attribute_list + [
                                 'Số lượng', 'Price Unit', 'Subtotal', 'Trạng thái', ]
        summary_header = ['Mã báo giá', 'Ngày đặt hàng', 'Mã khách hàng', 'Khách hàng', 'Tỉnh/Thành phố',
                          'SĐT Khách hàng', 'Nhân viên bán hàng',
                          'Created by', 'Validate by', 'Tổng', 'Ghi chú', 'Hình thức thanh toán', 'Mã biến thể nội bộ',
                          'Tên sản phẩm'] + attribute_list + [
                             'Số lượng', 'Price Unit', 'Subtotal', 'Trạng thái đơn hàng', 'Trạng thái hoạt động']
        summary_header_return = ['Reference Return', 'Thời gian tạo', 'Mã khách hàng', 'Khách hàng', 'SDT khách hàng',
                                 'Nhân viên bán hàng', 'Created by', 'Validate by', 'Ghi chú', 'Lý do trả hàng',
                                 'Sale Order', 'Tổng', 'Mã nội bộ',
                                 'Tên sản phẩm', 'Số lượng', 'Price Unit', 'Subtotal', 'Trạng thái đơn hàng',
                                 'Trạng thái hoạt động']
        row = 0
        if type and type == 'return':
            [worksheet.write(row, header_cell, unicode(summary_header_return[header_cell], "utf-8"), body_bold_color)
             for
             header_cell in range(0, len(summary_header_return)) if summary_header_return[header_cell]]

            for quotaion_id in quotaion_ids:
                state = dict(self.env['sale.order'].fields_get(allfields=['state'])['state'][
                                 'selection'])
                tt_donhang = dict(self.env['sale.order'].fields_get(allfields=['trang_thai_dh'])['trang_thai_dh'][
                                      'selection'])
                confirmation_date = ''
                if quotaion_id.confirmation_date:
                    confirmation_date = self._get_datetime_utc(quotaion_id.confirmation_date)
                for line in quotaion_id.order_line:
                    row += 1
                    worksheet.write(row, 0, quotaion_id.name, text_style)
                    worksheet.write(row, 1, confirmation_date, text_style)
                    worksheet.write(row, 2, quotaion_id.partner_id.ref or '', text_style)
                    worksheet.write(row, 3, quotaion_id.partner_id.name, text_style)
                    worksheet.write(row, 4, quotaion_id.partner_id.phone or '', text_style)
                    worksheet.write(row, 5, quotaion_id.user_id.name, text_style)
                    worksheet.write(row, 6, quotaion_id.create_uid.name or '', text_style)
                    worksheet.write(row, 7, quotaion_id.confirm_user_id.name or '', text_style)
                    worksheet.write(row, 8, quotaion_id.note or '', text_style)
                    worksheet.write(row, 9, quotaion_id.reason_cancel.name or '', text_style)
                    sale_order = ', '.join([order.name for order in quotaion_id.sale_order_return_ids])
                    worksheet.write(row, 10, sale_order, body_bold_color_number)
                    worksheet.write(row, 11, quotaion_id.amount_total, body_bold_color_number)
                    worksheet.write(row, 12, line.product_id.default_code or '', text_style)
                    worksheet.write(row, 13, line.product_id.name or '', text_style)
                    worksheet.write(row, 14, line.product_uom_qty or '', text_style)
                    worksheet.write(row, 15, line.price_unit or '', body_bold_color_number)
                    worksheet.write(row, 16, line.price_total, body_bold_color_number)
                    worksheet.write(row, 17, state.get(quotaion_id.state), text_style)
                    worksheet.write(row, 18, tt_donhang.get(quotaion_id.trang_thai_dh), text_style)

            workbook.close()
            output.seek(0)
            response.stream.write(output.read())
            output.close()
        if type and type == 'sale':
            [worksheet.write(row, header_cell, unicode(str(summary_header[header_cell]), "utf-8"), body_bold_color) for
             header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

            for quotaion_id in quotaion_ids:
                state = dict(self.env['sale.order'].fields_get(allfields=['state'])['state'][
                                 'selection'])
                tt_donhang = dict(self.env['sale.order'].fields_get(allfields=['trang_thai_dh'])['trang_thai_dh'][
                                      'selection'])
                for line in quotaion_id.order_line:
                    thuoc_tinh_list = []
                    for attribute in attribute_list:
                        check = False
                        for product_attribute in line.product_id.attribute_value_ids:
                            if attribute == product_attribute.attribute_id.name:
                                thuoc_tinh_list.append(product_attribute.name)
                                check = True
                                break
                        if not check:
                            thuoc_tinh_list.append('')
                    confirmation_date = ''
                    if quotaion_id.confirmation_date:
                        confirmation_date = self._get_datetime_utc(quotaion_id.confirmation_date)
                    row += 1
                    col = 13
                    worksheet.write(row, 0, quotaion_id.name, text_style)
                    worksheet.write(row, 1, confirmation_date, text_style)
                    worksheet.write(row, 2, quotaion_id.partner_id.ref or '', text_style)
                    worksheet.write(row, 3, quotaion_id.partner_id.name, text_style)
                    worksheet.write(row, 4, quotaion_id.partner_id.feosco_city_id.name, text_style)
                    worksheet.write(row, 5, quotaion_id.partner_id.phone or '', text_style)
                    worksheet.write(row, 6, quotaion_id.user_id.name, text_style)
                    worksheet.write(row, 7, quotaion_id.create_uid.name or '', text_style)
                    worksheet.write(row, 8, quotaion_id.confirm_user_id.name or '', text_style)
                    worksheet.write(row, 9, quotaion_id.amount_total, body_bold_color_number)
                    worksheet.write(row, 10, quotaion_id.note or '', text_style)
                    worksheet.write(row, 11, quotaion_id.payment_method.display_name or '', text_style)
                    worksheet.write(row, 12, line.product_id.default_code or '', text_style)
                    worksheet.write(row, 13, line.product_id.name or '', text_style)
                    for thuoc_tinh in thuoc_tinh_list:
                        col += 1
                        worksheet.write(row, col, thuoc_tinh or '', text_style)
                    col += 1
                    worksheet.write(row, col, line.product_uom_qty or '', text_style)
                    col += 1
                    worksheet.write(row, col, line.price_unit or '', body_bold_color_number)
                    col += 1
                    worksheet.write(row, col, line.price_total, body_bold_color_number)
                    col += 1
                    worksheet.write(row, col, state.get(quotaion_id.state), text_style)
                    col += 1
                    worksheet.write(row, col, tt_donhang.get(quotaion_id.trang_thai_dh), text_style)

            workbook.close()
            output.seek(0)
            response.stream.write(output.read())
            output.close()
        if not type:
            [worksheet.write(row, header_cell, unicode(str(summary_header_quo[header_cell]), "utf-8"), body_bold_color)
             for
             header_cell in range(0, len(summary_header_quo)) if summary_header_quo[header_cell]]

            for quotaion_id in quotaion_ids_:
                state = dict(self.env['sale.order'].fields_get(allfields=['state'])['state'][
                                 'selection'])
                tt_donhang = dict(self.env['sale.order'].fields_get(allfields=['trang_thai_dh'])['trang_thai_dh'][
                                      'selection'])
                for line in quotaion_id.order_line:
                    thuoc_tinh_list = []
                    for attribute in attribute_list:
                        check = False
                        for product_attribute in line.product_id.attribute_value_ids:
                            if attribute == product_attribute.attribute_id.name:
                                thuoc_tinh_list.append(product_attribute.name)
                                check = True
                                break
                        if not check:
                            thuoc_tinh_list.append('')
                    confirmation_date = ''
                    if quotaion_id.confirmation_date:
                        confirmation_date = self._get_datetime_utc(quotaion_id.confirmation_date)
                    row += 1
                    col = 10
                    worksheet.write(row, 0, quotaion_id.name, text_style)
                    worksheet.write(row, 1, confirmation_date, text_style)
                    worksheet.write(row, 2, quotaion_id.partner_id.ref or '', text_style)
                    worksheet.write(row, 3, quotaion_id.partner_id.name, text_style)
                    worksheet.write(row, 4, quotaion_id.partner_id.phone or '', text_style)
                    worksheet.write(row, 5, quotaion_id.user_id.name, text_style)
                    worksheet.write(row, 6, quotaion_id.create_uid.name or '', text_style)
                    worksheet.write(row, 7, quotaion_id.amount_total, body_bold_color_number)
                    worksheet.write(row, 8, quotaion_id.note or '', text_style)
                    worksheet.write(row, 9, line.product_id.default_code or '', text_style)
                    worksheet.write(row, 10, line.product_id.name or '', text_style)
                    for thuoc_tinh in thuoc_tinh_list:
                        col += 1
                        worksheet.write(row, col, thuoc_tinh or '', text_style)
                    col += 1
                    worksheet.write(row, col, line.product_uom_qty or '', text_style)
                    col += 1
                    worksheet.write(row, col, line.price_unit or '', body_bold_color_number)
                    col += 1
                    worksheet.write(row, col, line.price_total, body_bold_color_number)
                    col += 1
                    worksheet.write(row, col, state.get(quotaion_id.state), text_style)

            workbook.close()
            output.seek(0)
            response.stream.write(output.read())
            output.close()

    @api.multi
    def print_excel(self):
        self.ensure_one()

        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        string_sheet = 'Bao Gia'
        worksheet = workbook.add_worksheet(string_sheet)
        bold = workbook.add_format({'bold': True})

        merge_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': '16'})
        header_bold_color = workbook.add_format({
            'bold': True,
            'font_size': '14',
            'align': 'center',
            'valign': 'vcenter'
        })
        header_bold_border_color = workbook.add_format({
            'bold': True,
            'font_size': '14',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        body_bold_color = workbook.add_format({
            'bold': False,
            'font_size': '14',
            'align': 'left',
            'valign': 'vcenter'
        })
        body_bold_center_color = workbook.add_format({
            'bold': False,
            'font_size': '14',
            'align': 'center',
            'valign': 'vcenter'
        })
        body_bold_border_color = workbook.add_format({
            'bold': False,
            'font_size': '14',
            'align': 'left',
            'valign': 'vcenter',
            'border': 1
        })
        money = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
        })
        # back_color =
        # back_color_date =

        worksheet.merge_range('A1:D1', self.company_id.name, body_bold_color)
        worksheet.merge_range('A2:D2', self.company_id.street, body_bold_color)

        string_header = "BÁO GIÁ"
        worksheet.merge_range('C3:E3', unicode(string_header, "utf-8"), merge_format)
        date = datetime.strptime(self.confirmation_date, DEFAULT_SERVER_DATETIME_FORMAT)
        string = "Ngày %s tháng %s năm %s" % (date.day, date.month, date.year)
        worksheet.merge_range('C4:E4', unicode(string, "utf-8"), header_bold_color)

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 20)

        worksheet.merge_range('A5:F5', 'Người mua:', body_bold_color)
        worksheet.merge_range('A6:F6', 'Tên khách hàng: %s' % (self.partner_id.name), body_bold_color)
        worksheet.merge_range('A7:F7', 'Địa chỉ: %s' % (self.partner_id.street), body_bold_color)
        worksheet.merge_range('A8:F8', 'Diễn giải: %s' % (self.note or ('Bán hàng %s' % (self.partner_id.name))),
                              body_bold_color)
        worksheet.merge_range('A9:F9', 'Điện thoại: %s' % (self.partner_id.phone), body_bold_color)

        worksheet.write(4, 6, 'Số: %s' % (self.name), body_bold_color)
        worksheet.write(5, 6, 'Loại tiền: VND', body_bold_color)

        row = 10
        count = 0
        summary_header = ['STT', 'Mã hàng', 'Tên hàng', 'Đơn vị', 'Số lượng', 'Đơn giá', 'Thành tiền']
        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_border_color) for
         header_cell in
         range(0, len(summary_header)) if summary_header[header_cell]]
        no = 0
        for line in self.order_line:
            no += 1
            row += 1
            count += 1
            worksheet.write(row, 0, no, body_bold_border_color)
            worksheet.write(row, 1, line.product_id.default_code, body_bold_border_color)
            worksheet.write(row, 2, line.product_id.name, body_bold_border_color)
            worksheet.write(row, 3, line.product_uom.name, body_bold_border_color)
            worksheet.write(row, 4, line.product_uom_qty, money)
            worksheet.write(row, 5, line.final_price, money)
            worksheet.write(row, 6, line.price_subtotal, money)
        row += 1
        # worksheet.merge_range('A9:F9', 'Điện thoại: %s' % (self.partner_id.phone), body_bold_color)
        worksheet.merge_range(row, 0, row, 5, unicode("Cộng", "utf-8"), body_bold_border_color)
        worksheet.write(row, 6, self.amount_untaxed, money)
        row += 1
        worksheet.merge_range(row, 0, row, 5, unicode("Cộng tiền hàng", "utf-8"), body_bold_border_color)
        worksheet.write(row, 6, self.amount_untaxed, money)
        row += 1
        worksheet.merge_range(row, 0, row, 1, unicode("Thuế suất GTGT", "utf-8"), body_bold_border_color)
        worksheet.write(row, 2, '', money)
        worksheet.merge_range(row, 3, row, 5, unicode("Tiền suất GTGT", "utf-8"), body_bold_border_color)
        worksheet.write(row, 6, self.amount_tax, money)
        row += 1
        worksheet.merge_range(row, 3, row, 5, unicode("Tổng thanh toán", "utf-8"), body_bold_border_color)
        worksheet.write(row, 6, self.amount_total, money)
        row += 1
        string = "Số tiền viết bằng chữ: %s đồng."
        string = unicode(string, "utf-8")
        string = string % self.total_text
        worksheet.merge_range(row, 0, row, 6, string, body_bold_color)
        row += 1
        string = "Ngày %s tháng %s năm %s" % (date.day, date.month, date.year)
        worksheet.write(row, 5, unicode(string, "utf-8"), body_bold_center_color)
        row += 2
        worksheet.merge_range(row, 0, row, 1, unicode("Người nhận hàng", "utf-8"), header_bold_color)
        worksheet.write(row, 2, unicode("Kho", "utf-8"), header_bold_color)
        worksheet.merge_range(row, 3, row, 4, unicode("Người lập phiếu", "utf-8"), header_bold_color)
        worksheet.merge_range(row, 5, row, 6, unicode("Giám đốc", "utf-8"), header_bold_color)
        row += 1
        worksheet.merge_range(row, 0, row, 1, unicode("(Ký, họ tên)", "utf-8"), body_bold_center_color)
        worksheet.write(row, 2, unicode("(Ký, họ tên)", "utf-8"), body_bold_center_color)
        worksheet.merge_range(row, 3, row, 4, unicode("(Ký, họ tên)", "utf-8"), body_bold_center_color)
        worksheet.merge_range(row, 5, row, 6, unicode("(Ký, họ tên)", "utf-8"), body_bold_center_color)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'DonHangExcel.xlsx', 'datas_fname': 'DonHangExcel.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return {"type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url)}

    @api.multi
    def update_invoice_so(self):
        ids = [8382]
        orderlines = self.browse(ids)
        for order in orderlines:
            for invoice_id in order.invoice_ids:
                if invoice_id.state == 'draft':
                    print
                    "----------------" + str(order.id)
                if invoice_id.state == 'open':
                    if invoice_id.move_id and datetime.strptime(order.date_order,
                                                                DEFAULT_SERVER_DATETIME_FORMAT).date() != datetime.strptime(
                        invoice_id.move_id.date, DEFAULT_SERVER_DATE_FORMAT).date():
                        self._cr.execute("""UPDATE account_move SET date='%s' WHERE id=%s""" % (
                            datetime.strptime(order.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                                DEFAULT_SERVER_DATE_FORMAT)
                            , invoice_id.move_id.id))
                        for move_line in invoice_id.move_id.line_ids:
                            self._cr.execute("""UPDATE account_move_line SET date='%s' WHERE id=%s""" % (
                                datetime.strptime(order.date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(
                                    DEFAULT_SERVER_DATE_FORMAT)
                                , move_line.id))
                            print
                            "----------------" + str(order.id)
        for order in orderlines:
            if order.amount_total > 0 and order.invoice_ids and (len(orderlines) == 1 or order.amount_total != sum(
                    order.invoice_ids.mapped('amount_total')) or any(
                product_id not in order.invoice_ids.mapped('invoice_line_ids').mapped('product_id')
                for product_id in order.order_line.mapped('product_id'))):
                if order.invoice_ids and all(invoice.state in ['draft', 'open'] for invoice in order.invoice_ids):
                    invoice_line_ids = order.invoice_ids.mapped('invoice_line_ids')
                    for invoice_line_id in invoice_line_ids:
                        if not invoice_line_id.sale_line_ids:
                            self._cr.execute("""DELETE FROM account_invoice_line WHERE id=%s""" % (invoice_line_id.id))
                        else:
                            order_line_id = invoice_line_id.sale_line_ids[0]
                            if order_line_id:
                                invoice_line_id.write({
                                    'quantity': order_line_id.product_uom_qty,
                                    'discount': order_line_id.discount,
                                    'price_unit': order_line_id.price_unit,
                                    'price_discount': order_line_id.price_discount,
                                    'invoice_line_tax_ids': [(6, 0, order_line_id.tax_id.ids)],
                                })
                                invoice_line_id._compute_price()
                                if order_line_id.product_id != invoice_line_id.product_id:
                                    invoice_line_id.product_id = order_line_id.product_id
                                    invoice_line_id.name = order_line_id.name
                    if len(order.order_line) > len(invoice_line_ids):
                        if not order.sale_order_return:
                            for order_line_id in (order.order_line - invoice_line_ids.mapped('sale_line_ids')):
                                if order_line_id.qty_to_invoice > 0:
                                    order_line_id.invoice_line_create(order.invoice_ids[0].id,
                                                                      order_line_id.qty_to_invoice)
                        else:
                            new_lines = self.env['account.invoice.line']
                            for order_line_id in (order.order_line - invoice_line_ids.mapped('sale_line_ids')):
                                account_id = self.env['account.account'].search([('code', '=', '5213')],
                                                                                limit=1).id or False
                                if line.product_id or line.quantity != 0:
                                    data = {
                                        'product_id': line.product_id.id,
                                        'quantity': line.product_uom_qty,
                                        'uom_id': line.product_uom.id,
                                        'price_unit': line.price_unit,
                                        'discount': line.discount,
                                        'price_discount': line.price_discount,
                                        'invoice_line_tax_ids': [(6, 0, line.tax_id.ids)],
                                        'name': line.product_id.display_name,
                                        'account_id': account_id,
                                        'sale_line_ids': [(6, 0, line.ids)]
                                    }
                                    data['quantity'] = line.product_uom_qty
                                    new_line = new_lines.new(data)
                                    new_lines += new_line
                            order_line_id.invoice_ids[0].invoice_line_ids += new_lines
                    order.invoice_ids.compute_taxes()
            check_diff = float_compare(sum(order.invoice_ids.mapped('move_id').mapped('line_ids').mapped('credit')),
                                       order.amount_total, precision_digits=2)
            if order.amount_total > 0 and order.invoice_ids.filtered(lambda inv: inv.move_id) and check_diff != 0:
                for invoice_id in order.invoice_ids.filtered(lambda inv: inv.move_id):
                    move_line = self.env['account.move.line']
                    line_not_ext = self.env['account.move.line']
                    move_line_data = invoice_id.get_move_line_from_inv()
                    for line_data in move_line_data:
                        line_data = line_data[2]
                        move_line_change = (invoice_id.move_id.mapped('line_ids') - move_line).filtered(
                            lambda mvl: mvl.product_id.id == line_data.get('product_id', False)
                                        and mvl.account_id.id == line_data.get('account_id', False))
                        if move_line_change:
                            for line in move_line_change:
                                if line.id not in line_not_ext.ids:
                                    line_not_ext += line
                                if line.credit != line_data.get('credit', 0) or line.debit != line_data.get('debit', 0):
                                    self._cr.execute("""UPDATE account_move_line SET credit=%s, debit=%s
                                                       WHERE id=%s""" % (
                                        line_data.get('credit', 0) or 0, line_data.get('debit', 0) or 0, line.id))
                                    self._cr.commit()
                                    move_line += line
                                    line.update_open_amount_residual()
                                    break
                        else:
                            script = """INSERT INTO account_move_line (ref,name, invoice_id, tax_line_id, credit,product_uom_id,currency_id,product_id,debit
                                                         ,amount_currency,quantity,partner_id,account_id,move_id,date_maturity)
                                                                VALUES ('%s','%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'%s')""" % (
                                invoice_id.origin, line_data['name'],
                                line_data['invoice_id'] or invoice_id.id, line_data['tax_line_id'] or 'NULL',
                                line_data['credit'] or 0, line_data['product_uom_id'] or 'NULL',
                                line_data['currency_id'] or 'NULL', line_data['product_id'] or 'NULL',
                                line_data['debit'] or 0, line_data['amount_currency'] or 0, line_data['quantity'] or 0,
                                line_data['partner_id'] or 'NULL', line_data['account_id'], invoice_id.move_id.id,
                                fields.Date.context_today(self))
                            self._cr.execute(script)
                            self._cr.commit()
                    for line_remove in (invoice_id.move_id.mapped('line_ids') - line_not_ext):
                        self._cr.execute("""DELETE FROM account_move_line WHERE id=%s""" % (line_remove.id))
                    if invoice_id.payments_widget == 'false':
                        invoice_id.residual = invoice_id.amount_total
                    else:
                        raise UserError("Bạn không thể cập nhật hoá đơn đã thanh toán một phần: %s từ đơn hàng %s" % (
                            invoice_id.number, order.name))
                        # invoice_id._compute_residual()

    @api.multi
    def update_user_validate(self):
        for order in self.env['sale.order'].search([('sale_order_return', '=', True), ('confirm_user_id', '=', False)]):
            subtype = self.env.ref('sale.mt_order_confirmed')
            user_validate = self.env['mail.message'].search(
                [('model', '=', 'sale.order'), ('res_id', '=', order.id), ('subtype_id', '=', subtype.id)], limit=1)
            if user_validate:
                order.confirm_user_id = user_validate.write_uid


class tts_transporter_route_ihr(models.Model):
    _inherit = 'tts.transporter.route'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if 'partner_id' in self._context:
            partner_id = self._context.get('partner_id', False)
            partner_id = self.env['res.partner'].browse(partner_id)
            if partner_id:
                transport_route_ids = self.env['tts.transporter.route'].search([
                    ('feosco_city_id', '=', partner_id.feosco_city_id.id),
                    ('feosco_district_id', '=', partner_id.feosco_district_id.id),
                ])
                if transport_route_ids:
                    args += [('id', 'in', transport_route_ids.ids)]
        return super(tts_transporter_route_ihr, self).name_search(name=name, args=args, operator=operator, limit=limit)
