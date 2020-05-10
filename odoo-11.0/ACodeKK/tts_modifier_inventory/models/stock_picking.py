# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from odoo.exceptions import ValidationError


class stock_picking_ihr(models.Model):
    _inherit = 'stock.picking'

    state_pick = fields.Selection(
        [('draft', 'Draft'),
         ('waiting_pick', 'Waiting'),
         ('ready_pick', 'Ready'),
         ('picking', 'Picking'),
         ('done', 'Done'),
         ('cancel', 'Cancel')], default='waiting_pick',
        string="Pick state")
    state_pack = fields.Selection(
        [('draft', 'Draft'),
         ('waiting_another_operation', 'Waiting another operation'),
         ('waiting_pack', 'Waiting'),
         ('packing', 'Packing'),
         ('done', 'Done'),
         ('cancel', 'Cancel')], default='draft',
        string="Pack state")
    state_delivery = fields.Selection(
        [('draft', 'Draft'),
         ('waiting_another_operation', 'Waiting another operation'),
         ('waiting_delivery', 'Waiting'),
         ('delivery', 'Delivering'),
         ('done', 'Done'),
         ('cancel', 'Cancel')],
        default='waiting_delivery',
        string="Delivery state")
    check_is_pick = fields.Boolean(compute='_get_check_is_pick')
    check_is_pack = fields.Boolean(compute='_get_check_is_pick')
    check_is_delivery = fields.Boolean(compute='_get_check_is_pick')
    kich_thuoc_don_hang = fields.Many2one('inventory.package.size', string="Kích thước đơn hàng")
    user_pick_id = fields.Many2one('res.users',string='Nhân viên lấy hàng')
    user_pack_id = fields.Many2one('res.users', string='Nhân viên đóng gói')
    user_delivery_id = fields.Many2one('res.users', string='Nhân viên giao hàng')
    sale_id = fields.Many2one(string='Sale Order')
    user_sale_id = fields.Many2one('res.users',string='Nhân viên bán hàng',readonly=True)
    user_perform_id = fields.Many2one('res.users',string='Người thực hiện')
    pick_have_update = fields.Boolean(default=False)
    delivery_id = fields.Many2one('res.partner', 'Người giao', required=False)
    receive_id = fields.Many2one('res.partner', 'Người nhận', required=False)
    origin_sub = fields.Char(compute='_get_origin_sub', string='Source Document')

    @api.multi
    def _get_origin_sub(self):
        for rec in self:
            if rec.origin:
                rec.origin_sub = rec.origin.split(':')[0]

    def get_thoi_gian_tao_phieu(self):
        resuft = ''
        for line in self.stock_picking_log_ids:
            if line.status_changed:
                state = line.status_changed.split('->')[1].strip()
                if state == 'Ready':
                    resuft = self._get_datetime_utc(line.time_log)
        return resuft

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

    @api.model
    def get_receipt_report_data(self):
        pick_data = []
        for line in self.move_lines:
            if line.product_id.default_code in list(map(lambda x: x['product_code'], pick_data)):
                for line_data in pick_data:
                    if line.product_id.default_code == line_data.get('product_code',False):
                        line_data['product_uom_qty'] +=  int(line.product_uom_qty)
            else:
                variants = [line.product_id.name]
                mau = ''
                for attr in line.product_id.attribute_value_ids:
                    if attr.attribute_id.name in ('Size','size'):
                        variants.append(('Size ' + attr.name))
                    else:
                        if  attr.attribute_id.name in ('Màu','màu'):
                            mau = attr.name
                        variants.append((attr.name))

                data = {
                    'product_code' : line.product_id.default_code,
                    'name' : line.product_id.name,
                    'product_name': self.get_product_name_report(line.product_id),
                    'product_uom_qty': int(line.product_uom_qty),
                    'mau' : mau,
                }
                pick_data.append(data)
        pick_data = sorted(pick_data, key=lambda elem: "%s %s %s" % (elem['name'],elem['mau'],elem['product_code']))
        return pick_data

    @api.model
    def get_pick_report_data(self):
        pick_data = []
        for line in self.move_lines:
            if line.product_id.default_code in list(map(lambda x: x['product_code'], pick_data)):
                for line_data in pick_data:
                    if line.product_id.default_code == line_data.get('product_code',False):
                        line_data['product_uom_qty'] +=  int(line.product_uom_qty)
            else:
                variants = [line.product_id.name]
                mau = ''
                size = 0
                for attr in line.product_id.attribute_value_ids:
                    if attr.attribute_id.name in ('Size','size'):
                        variants.append(('Size ' + attr.name))
                        try:
                            size = int(attr.name)
                        except:
                            size = attr.name
                            if size == 'L':
                                size = 3
                            elif size == 'M':
                                size = 2
                            elif size == 'S':
                                size = 1
                            elif size == 'XL':
                                size = 4
                            else:
                                size = 5
                    else:
                        if attr.attribute_id.name in ('Màu','màu'):
                            mau = attr.name
                        variants.append((attr.name))

                product_name = ' - '.join(variants)
                data = {
                    'product_code' : line.product_id.default_code,
                    'name' : line.product_id.name,
                    'product_name': product_name,
                    'product_uom_qty': int(line.product_uom_qty),
                    'row_span_x' : 1,
                    'row_span_y' : 1,
                    'mau' : mau,
                    'size' : size,
                }
                if line.product_id.location_ids:
                    data.update({
                        'x' : line.product_id.location_ids[0].posx,
                        'y': line.product_id.location_ids[0].posy,
                        'location_name' : line.product_id.location_ids[0].name,
                        'location_display_name' : line.product_id.location_ids[0].display_name
                    })
                else:
                    data.update({
                        'x' : 0,
                        'y' : 0,
                        'location_name': '',
                        'location_display_name': '',
                    })
                pick_data.append(data)
        pick_data = sorted(pick_data, key=lambda elem: "%02d %02d %s %s %s %02d %s" % (elem['x'],elem['y'],elem['location_name'],elem['name'],elem[
            'mau'], elem['size'], elem['product_code']))
        for i in range(0,len(pick_data)):
            row_span_y = 1
            for j in range(i+1,len(pick_data)):
                if pick_data[i].get('x',False) == pick_data[j].get('x',False):
                    if pick_data[i].get('y',False) and pick_data[i].get('y',False) == pick_data[j].get('y',False):
                        pick_data[j].update({
                            'y' : -1
                        })
                        row_span_y += 1
                    else:
                        break
                else:
                    break
            if row_span_y != 1:
                pick_data[i].update({
                    'row_span_y': row_span_y
                })

        for i in range(0,len(pick_data)):
            row_span_x = 1
            for j in range(i+1,len(pick_data)):
                if pick_data[i].get('x', False) and pick_data[i].get('x', False) == pick_data[j].get('x', False):
                    pick_data[j].update({
                        'x': -1
                    })
                    row_span_x += 1
                else:
                    break
            if row_span_x != 1:
                pick_data[i].update({
                    'row_span_x': row_span_x
                })

        return pick_data

    # TODO button picking delivery
    @api.multi
    def delivery_action_confirm(self):
        for rec in self:
            if rec.state_delivery == 'draft':
                rec.state_delivery = 'waiting_delivery'

    @api.multi
    def delivery_action_assign(self):
        context = self.env.context.copy() or {}
        context.update({
            'skip_account_move_line': True,
        })
        for rec in self:
            if rec.state == 'assigned':
                rec.state_delivery = 'delivery'
                return rec.with_context(context).do_new_transfer()
            else:
                rec.action_confirm()
                rec.action_assign()
                if rec.state == 'assigned':
                    rec.state_delivery = 'delivery'
                    return rec.with_context(context).do_new_transfer()

    @api.multi
    def delivery_action_do_new_transfer(self):
        for rec in self:
            rec.state_delivery = 'done'

    @api.multi
    def do_new_transfer_modifier(self):
        action = self.env.ref('tts_modifier_inventory.delivery_send_sms_action').read()[0]
        action['context'] = {'default_picking_id': self.id}
        return action

    # TODO button picking pack
    @api.multi
    def pack_action_confirm(self):
        for rec in self:
            if rec.state_pack == 'draft':
                rec.state_pack = 'waiting_pack'

    @api.multi
    def pack_action_assign(self):
        for rec in self:
            rec.action_confirm()
            rec.state_pack = 'packing'

    @api.multi
    def pack_action_do_new_transfer(self):
        for rec in self:
            if rec.state == 'assigned':
                rec.state_pack = 'done'
                return rec.do_new_transfer()
            else:
                rec.action_assign()
                if rec.state == 'assigned':
                    rec.state_pack = 'done'
                    return rec.do_new_transfer()

    #TODO button picking pick
    @api.multi
    def pick_action_confirm(self):
        for rec in self:
            if rec.state_pick == 'draft':
                rec.state_pick = 'waiting_pick'
            elif rec.state_pick == 'waiting_pick':
                rec.state_pick = 'ready_pick'

    @api.multi
    def pick_action_assign(self):
        for rec in self:
            if rec.state_pick not in ('done', 'cancel'):
                rec.action_confirm()
                rec.state_pick = 'picking'

    @api.multi
    def open_popup_confirm(self):
        action = self.env.ref('tts_modifier_inventory.popup_confirm_pick_action').read()[0]
        action['context'] = {'default_picking_pick_id': self.id}
        return action

    @api.multi
    def pick_action_do_new_transfer(self):
        for rec in self:
            if rec.pick_have_update:
                action = self.env.ref('tts_modifier_inventory.popup_confirm_pick_action').read()[0]
                action['context'] = {'default_picking_pick_id': rec.id}
                return action
            else:
                if rec.state == 'assigned':
                    rec.state_pick = 'done'
                    return rec.do_new_transfer()
                else:
                    rec.action_assign()
                    if rec.state == 'assigned':
                        rec.state_pick = 'done'
                        return rec.do_new_transfer()

    @api.multi
    @api.onchange('picking_type_id')
    def _get_check_is_pick(self):
        for rec in self:
            rec.check_is_pick = False
            rec.check_is_pack = False
            rec.check_is_delivery = False
            if rec.picking_type_id and rec.picking_type_id.sequence_id:
                location_pack_zone = self.env.ref('stock.location_pack_zone')
                stock_location_output = self.env.ref('stock.stock_location_output')
                if 'PICK' in rec.picking_type_id.sequence_id.prefix or rec.picking_type_id.default_location_dest_id == location_pack_zone:
                    rec.check_is_pick = True
                elif 'PACK' in rec.picking_type_id.sequence_id.prefix or rec.picking_type_id.default_location_src_id == location_pack_zone:
                    rec.check_is_pack = True
                elif 'OUT' in rec.picking_type_id.sequence_id.prefix and rec.picking_type_id.default_location_src_id == stock_location_output:
                    rec.check_is_delivery = True

    @api.model
    def create(self, val):
        res = super(stock_picking_ihr, self).create(val)
        if res.check_is_pick and self._context.get('create_from_sale_order', False):
            self.env['inventory.history'].create({
                'name': self._context.get('create_from_sale_order', False),
                'thoi_gian_tao_pick': datetime.now(),
                'user_tao_pick': self._uid,
            })
        elif res.check_is_pack and self._context.get('create_from_sale_order', False):
            res.state_pack = 'waiting_another_operation'

        elif res.check_is_delivery and self._context.get('create_from_sale_order', False):
            res.state_delivery = 'waiting_another_operation'
        return res

    def update_inventory_history(self, sale_id, field, user_field):
        inventory_history_id = self.env['inventory.history'].search([('name', '=', sale_id.id)], order='id desc',
                                                                    limit=1)
        inventory_history_id.write({
            field: datetime.now(),
            user_field: self._uid,
        })

    @api.multi
    def write(self, val):
        for rec in self:
            if rec.check_is_pick and rec.sale_id and 'state_pick' in val:
                if val.get('state_pick', False) == 'waiting_pick':
                    rec.update_inventory_history(rec.sale_id, 'thoi_gian_bat_dau_pick', 'user_bat_dau_pick')
                elif val.get('state_pick', False) == 'done':
                    rec.update_inventory_history(rec.sale_id, 'thoi_gian_tao_pack', 'user_tao_pack')
            if rec.check_is_pack and rec.sale_id and 'state_pack' in val:
                if val.get('state_pack', False) == 'done':
                    rec.update_inventory_history(rec.sale_id, 'thoi_gian_tao_delivery', 'user_tao_delivery')
            if rec.check_is_delivery and rec.sale_id and 'state_delivery' in val:
                if val.get('state_delivery', False) == 'delivery':
                    rec.update_inventory_history(rec.sale_id, 'thoi_gian_bat_dau_delivery', 'user_bat_dau_delivery')
                elif val.get('state_delivery', False) == 'done':
                    rec.update_inventory_history(rec.sale_id, 'thoi_gian_hoan_tat_delivery', 'user_hoan_tat_delivery')

        res = super(stock_picking_ihr, self).write(val)
        return res


class sale_order_line_ihr(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _action_procurement_create(self):
        res = super(sale_order_line_ihr, self)._action_procurement_create()
        orders = list(set(x.order_id for x in self))
        for order in orders:
            check = False
            if order.payment_method.type == 'cash':
                check = True
            elif order.payment_method.type == 'bank' and order.trang_thai_tt == 'tt_1_phan' and order.delivery_method in (
            'delivery', 'warehouse'):
                check = True
            elif order.payment_method.type == 'bank' and order.trang_thai_tt == 'done_tt':
                check = True
            if check:
                picking_ids = order.picking_ids.filtered(lambda x: x.check_is_pick)
                for pick in picking_ids:
                    if pick.state_pick in ('draft','waiting_pick'):
                        pick.write({
                            'state_pick': 'ready_pick',
                        })
            picking_pick_ids = order.picking_ids.filtered(lambda x: x.check_is_pick)
            for pick in picking_pick_ids:
                if pick.state_pick in ('picking'):
                    pick.pick_have_update = True

            picking_pack_ids = order.picking_ids.filtered(lambda x: x.check_is_pack)
            for pack in picking_pack_ids:
                if pack.state_pack in ('waiting_pack', 'packing') and pack.state not in ('assigned') or pack.state_pack == 'draft':
                    pack.state_pack = 'waiting_another_operation'

            picking_out_ids = order.picking_ids.filtered(lambda x: x.check_is_delivery)
            for delivery in picking_out_ids:
                if delivery.state_pack in ('waiting_delivery', 'delivery','draft') and delivery.state not in ('assigned','done'):
                    delivery.state_delivery = 'waiting_another_operation'

        return res

class sale_order_ihr(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def write(self, val):
        res = super(sale_order_ihr, self).write(val)
        if val.get('payment_method',False) or val.get('trang_thai_tt',False):
            for order in self:
                check = False
                if order.payment_method.type == 'cash':
                    check = True
                elif order.payment_method.type == 'bank' and order.trang_thai_tt == 'tt_1_phan' and order.delivery_method in (
                        'delivery', 'warehouse'):
                    check = True
                elif order.payment_method.type == 'bank' and order.trang_thai_tt == 'done_tt':
                    check = True
                if check:
                    picking_ids = order.picking_ids.filtered(lambda x: x.check_is_pick)
                    for pick in picking_ids:
                        if pick.state_pick in ('draft', 'waiting_pick'):
                            pick.write({
                                'state_pick': 'ready_pick',
                            })
                else:
                    picking_ids = order.picking_ids.filtered(lambda x: x.check_is_pick)
                    for pick in picking_ids:
                        if pick.state_pick in ('ready_pick'):
                            pick.write({
                                'state_pick': 'waiting_pick',
                            })
        return res

class popup_confirm_pick(models.TransientModel):
    _name = 'popup.confirm.pick'

    xuat_kho_tang_cuong = fields.Selection([('no', 'No'),('yes', 'Yes')], string='Xuất kho tăng cường')
    picking_pick_id = fields.Many2one('stock.picking')

    @api.multi
    def action_confirm(self):
        self.picking_pick_id.pick_have_update = False
        return self.picking_pick_id.action_assign()



class delivery_send_sms(models.Model):
    _name = 'delivery.send.sms'

    picking_id = fields.Many2one('stock.picking', string='Picking')
    thoi_gian_giao_hang = fields.Datetime(string='Thời gian giao hàng', default=lambda self: fields.Datetime.now())
    nhan_vien_gia_hang = fields.Many2one('res.partner', string='Nhân viên giao hàng')
    nhan_vien_giao_hang = fields.Many2one('res.users', string='Nhân viên giao hàng')
    giao_hang_tang_cuong = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Giao hàng tăng cường')

    @api.model
    def default_get(self, fields):
        res = super(delivery_send_sms, self).default_get(fields)
        picking_id = res.get('picking_id',False)
        if picking_id:
            picking_id = self.env['stock.picking'].browse(picking_id)
            res['nhan_vien_giao_hang'] = picking_id.user_delivery_id.id
            res['giao_hang_tang_cuong'] = picking_id.giao_hang_tang_cuong
        return res

    @api.multi
    def do_new_transfer(self):
        if self.nhan_vien_giao_hang:
            self.picking_id.user_delivery_id = self.nhan_vien_giao_hang
            self.picking_id.giao_hang_tang_cuong = self.giao_hang_tang_cuong
        self.picking_id.delivery_action_do_new_transfer()
        if self.picking_id.sale_id.delivery_method == 'transport':
            mobile = self.picking_id.partner_id.mobile or self.picking_id.partner_id.phone
            if self.picking_id.partner_id and mobile:
                user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
                thoi_gian_giao_hang = datetime.strptime(self.thoi_gian_giao_hang, DEFAULT_SERVER_DATETIME_FORMAT)
                thoi_gian_giao_hang = pytz.utc.localize(thoi_gian_giao_hang).astimezone(user_tz).strftime(
                    '%H:%M %d/%m/%Y')

                content = "THETHAOSI da GUI HANG cho [%s] qua Nha Van Chuyen [%s] vao luc [%s]. Cam on Quy Khach. Hotline 0862860808" % \
                          (self.picking_id.partner_id.name,
                           self.picking_id.sale_id.transport_route_id.transporter_id.name,
                           thoi_gian_giao_hang)
                params = {
                    'Phone': mobile,
                    'Content': content
                }
                api_id = self.env.ref('tts_api.tts_esms_api_config')
                api_id._create_sms_partner(params)
            elif not mobile:
                raise ValidationError('Cần cấu hình số điện thoại cho khách hàng!')

class PushedFlowIhr(models.Model):
    _inherit = "stock.location.path"

    def _prepare_move_copy_values(self, move_to_copy, new_date):
        new_move_vals = super(PushedFlowIhr, self)._prepare_move_copy_values(move_to_copy, new_date)
        new_move_vals.update({
            'partner_id' : move_to_copy.picking_id.partner_id.id
        })

        return new_move_vals
