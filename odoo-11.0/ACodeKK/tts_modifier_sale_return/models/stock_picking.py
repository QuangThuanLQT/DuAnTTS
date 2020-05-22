# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class stock_move_inhr(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def action_done(self):
        res = super(stock_move_inhr, self).action_done()
        # for move in self:
        #     if move.picking_id.sale_id and move.picking_id.sale_id.sale_order_return:
        #         if move.move_dest_id.picking_id.state == 'assigned':
        #             move.move_dest_id.picking_id.do_unreserve()
        return res


class stock_picking_ihr(models.Model):
    _inherit = 'stock.picking'

    def _get_domain_user_pick(self):
        group_ql_kho = self.env.ref('tts_modifier_access_right.group_ql_kho').users
        group_soan_donggoi = self.env.ref('tts_modifier_access_right.group_soan_donggoi').users
        return [('id', 'in', group_ql_kho.ids + group_soan_donggoi.ids)]

    def _get_domain_user_delivery(self):
        group_ql_kho = self.env.ref('tts_modifier_access_right.group_ql_kho').users
        group_nv_giao_hang = self.env.ref('tts_modifier_access_right.group_nv_giao_hang').users
        return [('id', 'in', group_ql_kho.ids + group_nv_giao_hang.ids)]

    def _get_domain_user_receiver(self):
        group_ql_kho = self.env.ref('tts_modifier_access_right.group_ql_kho').users
        group_nv_nhap_hang = self.env.ref('tts_modifier_access_right.group_nv_nhap_hang').users
        return [('id', 'in', group_ql_kho.ids + group_nv_nhap_hang.ids)]

    is_picking_return = fields.Boolean(default=False)
    have_picking_return = fields.Boolean(default=False)
    reason_cancel = fields.Many2one('reason.cancel.sale', string='Nguyên nhân hủy', related='sale_id.reason_cancel')
    tra_hang_tang_cuong = fields.Selection([('no', 'No'), ('yes', 'Yes')], default='no', string='Trả hàng tăng cường',
                                           track_visibility='onchange')
    user_create_return = fields.Many2one('res.users', string='Nhân viên tạo trả hàng',
                                         related='sale_id.user_create_return')
    picking_from_sale_return = fields.Boolean(related='sale_id.sale_order_return')
    user_sale_id = fields.Many2one('res.users', string='Nhân viên bán hàng', compute='_get_user_sale', readonly=True)
    kiem_hang_nhap_tang_cuong = fields.Selection([('no', 'No'), ('yes', 'Yes')], default='no',
                                                 string='Kiểm hàng tăng cường',
                                                 track_visibility='onchange')
    user_pick_id = fields.Many2one(domain=_get_domain_user_pick)
    user_pack_id = fields.Many2one(domain=_get_domain_user_pick)
    user_delivery_id = fields.Many2one(domain=_get_domain_user_delivery)
    receiver = fields.Many2one(domain=_get_domain_user_receiver)
    user_checking_id = fields.Many2one(domain=_get_domain_user_receiver)

    @api.multi
    def _get_user_sale(self):
        for rec in self:
            if rec.sale_id and rec.sale_id.sale_order_return:
                if rec.sale_id.sale_order_return_ids:
                    rec.user_sale_id = rec.sale_id.sale_order_return_ids[0].confirm_user_id or \
                                       rec.sale_id.sale_order_return_ids[0].create_uid
            elif rec.sale_id and not rec.sale_id.sale_order_return:
                rec.user_sale_id = rec.sale_id.confirm_user_id or rec.sale_id.create_uid

    @api.multi
    def do_new_transfer(self):
        res = super(stock_picking_ihr, self).do_new_transfer()
        for rec in self:
            if not rec.is_picking_return and rec.check_is_pick:
                pack_id = rec.mapped('move_lines').mapped('move_dest_id').mapped('picking_id')
                if pack_id.state_pack == 'waiting_another_operation':
                    if pack_id:
                        pack_id.write({
                            'state_pack': 'waiting_pack',
                        })
            elif not rec.is_picking_return and rec.check_is_pack:
                delivery_id = rec.mapped('move_lines').mapped('move_dest_id').mapped('picking_id')
                if delivery_id:
                    if delivery_id.state_delivery == 'waiting_another_operation':
                        delivery_id.write({
                            'kich_thuoc_don_hang': rec.kich_thuoc_don_hang.id,
                            'state_delivery': 'waiting_delivery'
                        })

            if rec.is_picking_return and rec.check_is_delivery:
                picking_out = self.env['stock.picking'].search([('name', '=', rec.origin)], limit=1)
                move_pack = self.env['stock.move'].search([('move_dest_id', 'in', picking_out.move_lines.ids)])
                if move_pack:
                    picking_pack = move_pack.mapped('picking_id')
                    for pack in picking_pack:
                        # create return picking pack
                        # pack_obj = self.env['stock.return.picking'].with_context({'active_id': picking_pack.id})
                        # pack_return_data = pack_obj.sudo().default_get(pack_obj._fields)
                        # pack_return = pack_obj.create(pack_return_data)
                        # pack_return.create_returns()
                        picking_pack.create_picking_return()
            elif rec.is_picking_return and rec.check_is_pack:
                picking_pack = self.env['stock.picking'].search([('name', '=', rec.origin)], limit=1)
                move_pick = self.env['stock.move'].search([('move_dest_id', 'in', picking_pack.move_lines.ids)])
                if move_pick:
                    picking_pick = move_pick.mapped('picking_id')
                    for pick in picking_pick:
                        # create return picking pick
                        # pick_obj = self.env['stock.return.picking'].with_context({'active_id': pick.id})
                        # pick_return_data = pick_obj.sudo().default_get(pick_obj._fields)
                        # pick_return = pick_obj.create(pick_return_data)
                        # pick_return.create_returns()
                        pick.create_picking_return()
            elif rec.is_picking_return and rec.check_is_pick:
                picking_pick = rec.sale_id.picking_ids.filtered(lambda l: l.check_is_pick == True)
                if not any(picking.state not in ('done', 'cancel') for picking in picking_pick):
                    if rec.sale_id:
                        rec.sale_id.state = 'cancel'
            elif rec.sale_id and rec.picking_type_code == 'incoming' and rec.is_picking_return:
                receipt_id = rec.sale_id.picking_ids.filtered(lambda l: l.picking_type_code == 'incoming')
                if not any(picking.state not in ('done', 'cancel') for picking in receipt_id):
                    if rec.sale_id:
                        rec.sale_id.state = 'cancel'

        return res

    @api.multi
    def pick_action_assign(self):
        res = super(stock_picking_ihr, self).pick_action_assign()
        for rec in self:
            if rec.sale_id and rec.is_picking_return == False:
                order_state_id = self.env['sale.order.state'].search(
                    [('sale_id', '=', rec.sale_id.id), ('order_state', '=', 'picking')])
                if not order_state_id:
                    rec.order_state = 'picking'
                    order_state_id = self.env['sale.order.state'].create({
                        'sale_id': rec.sale_id.id,
                        'order_state': 'packing',
                        'date': datetime.now()
                    })
        return res

    @api.multi
    def delivery_action_assign(self):
        res = super(stock_picking_ihr, self).delivery_action_assign()
        for rec in self:
            if rec.sale_id and rec.is_picking_return == False:
                order_state_id = self.env['sale.order.state'].search(
                    [('sale_id', '=', rec.sale_id.id), ('order_state', '=', 'delivering')])
                if not order_state_id:
                    rec.order_state = 'delivering'
                    order_state_id = self.env['sale.order.state'].create({
                        'sale_id': rec.sale_id.id,
                        'order_state': 'delivering',
                        'date': datetime.now()
                    })
        return res

    @api.multi
    def delivery_action_do_new_transfer(self):
        res = super(stock_picking_ihr, self).delivery_action_do_new_transfer()
        for rec in self:
            if rec.sale_id and rec.is_picking_return == False:
                rec.order_state = 'delivered'
                order_state_id = self.env['sale.order.state'].search(
                    [('sale_id', '=', rec.sale_id.id), ('order_state', '=', 'delivered')])
                if not order_state_id:
                    order_state_id = self.env['sale.order.state'].create({
                        'sale_id': rec.sale_id.id,
                        'order_state': 'delivered',
                        'date': datetime.now()
                    })
        return res

    @api.multi
    def pick_action_do_new_transfer(self):
        res = super(stock_picking_ihr, self).pick_action_do_new_transfer()
        for rec in self:
            if rec.sale_id:
                rec.sale_id._get_trang_thai_dh()
        return res

    @api.multi
    def write(self, val):
        res = super(stock_picking_ihr, self).write(val)
        for rec in self:
            if (val.get('state_pick', False) or val.get('state_pack', False) or val.get('receipt_state', False) or \
                val.get('state_delivery', False) or val.get('internal_transfer_state',
                                                            False)) and rec.sale_id:
                rec.sale_id._get_trang_thai_dh()
        return res

    @api.model
    def create(self, val):
        res = super(stock_picking_ihr, self).create(val)
        if res.origin:
            if 'RT0' in res.origin:
                sale_id = self.env['sale.order'].search([('name', '=', res.origin)], limit=1)
                if sale_id and sale_id.sale_order_return == True:
                    sale_id._get_trang_thai_dh()
                    res.check_return_picking = True
            if 'SO' in res.origin:
                sale_id = self.env['sale.order'].search([('name', '=', res.origin)], limit=1)
                if sale_id and sale_id.sale_order_return == False:
                    sale_id._get_trang_thai_dh()
        return res

    def create_picking_return(self):
        for picking in self:
            picking_type_id = picking.picking_type_id.return_picking_type_id.id or picking.picking_type_id.id
            picking_data = {
                'move_lines': [],
                'picking_type_id': picking_type_id,
                'state': 'draft',
                'origin': picking.name,
                'location_id': picking.location_dest_id.id,
                'location_dest_id': self.location_id.id,
                'stock_picking_log_ids': [],
                'carrier_id': False,
                'carrier_price': 0.0,
                'is_picking_return': True
            }
            if picking.check_is_pick:
                picking_data['state_pick'] = 'ready_pick'
            elif picking.check_is_pack:
                picking_data['state_pack'] = 'waiting_pack'
            elif picking.check_is_delivery:
                picking_data['state_delivery'] = 'waiting_delivery'
            elif picking.picking_type_code == 'incoming':
                picking_data['receipt_state'] = 'reveive'
            new_picking = picking.copy(picking_data)
            i = 0
            move_lines = []
            print
            "begin loop ----%s" % (str(datetime.now()))
            for move_id in picking.move_lines:
                # move_id.move_dest_id.do_unreserve()
                # move_id.move_dest_id.write({'move_orig_ids': False})
                if move_id.origin_returned_move_id.move_dest_id.id and move_id.origin_returned_move_id.move_dest_id.state != 'cancel':
                    move_dest_id = move_id.origin_returned_move_id.move_dest_id.id
                else:
                    move_dest_id = False
                data = {
                    'product_id': move_id.product_id.id,
                    'product_uom_qty': move_id.product_uom_qty,
                    'product_uom': move_id.product_uom.id,
                    'picking_id': new_picking.id,
                    'state': 'draft',
                    'name': ' ',
                    'location_id': move_id.location_dest_id.id,
                    'location_dest_id': move_id.location_id.id,
                    'picking_type_id': picking_type_id,
                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                    'origin_returned_move_id': move_id.id,
                    'procure_method': 'make_to_stock',
                    'move_dest_id': move_dest_id,
                    'purchase_line_id': move_id.purchase_line_id.id,
                    'date': move_id.date,
                    'group_id': move_id.group_id.id,
                    'procurement_id': move_id.procurement_id.id,
                    'rule_id': move_id.rule_id.id,
                }
                # self.env['stock.move'].create(data)
                move_lines.append((0, 0, data))
                i += 1
                print
                "%s" % (i)
            new_picking.write({'move_lines': move_lines})
            picking.have_picking_return = True
            print
            "after create %s" % (str(datetime.now()))
            new_picking.action_confirm()
            new_picking.action_assign()


class ReturnPickingIhr(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def _create_returns(self):
        new_picking, picking_type_id = super(ReturnPickingIhr, self)._create_returns()
        new_picking = self.env['stock.picking'].browse(new_picking)
        if new_picking.check_is_pick:
            new_picking.state_pick = 'ready_pick'
            new_picking.stock_picking_log_ids.unlink()
        elif new_picking.check_is_pack:
            new_picking.state_pack = 'waiting_pack'
            new_picking.stock_picking_log_ids.unlink()
        elif new_picking.check_is_delivery:
            new_picking.state_delivery = 'waiting_delivery'
            new_picking.stock_picking_log_ids.unlink()
        elif new_picking.picking_type_code == 'incoming':
            new_picking.receipt_state = 'reveive'
            new_picking.stock_picking_log_ids.unlink()
        picking = self.env['stock.picking'].browse(self.env.context['active_id'])
        if not picking.is_picking_return:
            picking.have_picking_return = True
            new_picking.is_picking_return = True
        elif picking.is_picking_return:
            new_picking.is_picking_return = False
        return new_picking.id, picking_type_id
