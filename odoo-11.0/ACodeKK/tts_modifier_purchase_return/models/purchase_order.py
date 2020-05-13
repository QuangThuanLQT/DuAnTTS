# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from lxml import etree


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    reason_cancel = fields.Many2one('reason.cancel.purchase', string='Lý do', copy=False)
    check_show_cancel = fields.Boolean(compute='_get_show_cancel')
    location_return = fields.Selection([('normal', 'Kho Bình thường'),
                                        ('damaged', 'Kho hư hỏng')], string='Kho lưu trữ sản phẩm')
    location_id = fields.Many2one('stock.location', string='Source Location Zone')

    operation_state = fields.Selection([
        ('waiting_pick', 'Waiting to Pick'), ('ready_pick', 'Ready to Pick'), ('picking', 'Picking'),
        ('waiting_pack', 'Waiting to Pack'), ('packing', 'Packing'),
        ('waiting_delivery', 'Waiting to Delivery'), ('delivery', 'Delivering'),
        ('reveive', 'Receive'), ('waiting', 'Waiting to Check'), ('checking', 'Checking'),
        ('done', 'Done'),
        ('reverse_tranfer', 'Reverse Tranfer'),
        ('cancel', 'Cancel')
    ], string='Operation Status', store=True)
    state_return = fields.Selection([
        ('draft', 'Purchase Return Quotation'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Return'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', index=True, copy=True, compute='get_state_return')
    purchase_return_id = fields.Many2one('purchase.order', string='Purchase New', copy=False)
    delivery_method = fields.Selection(
        [('warehouse', 'Tới kho lấy hàng'),
         ('delivery', 'Giao tới tận nơi'),
         ('transport', 'Giao tới nhà xe'), ], string='Phương thức giao hàng', related='partner_id.delivery_method',
        readonly=True, store=True)
    transport_route_id = fields.Many2one('tts.transporter.route', string='Tuyến xe',
                                         related='partner_id.transport_route_id', readonly=True, store=True)
    delivery_scope_id = fields.Many2one('tts.delivery.scope', string='Phạm vi giao hàng',
                                        related='partner_id.delivery_scope_id', readonly=True, store=True)
    payment_address = fields.Char('Địa chỉ giao hàng', compute="get_payment_address", store=True)

    @api.depends('partner_id')
    def get_payment_address(self):
        for rec in self:
            if rec.delivery_method == 'delivery':
                rec.payment_address = "%s, %s, %s, %s" % (
                    rec.partner_id.street or '', rec.partner_id.feosco_ward_id.name or '',
                    rec.partner_id.feosco_district_id.name or '',
                    rec.partner_id.feosco_city_id.name or '')
            elif rec.delivery_method == 'transport':
                transport_route_ids = rec.env['tts.transporter.route'].search([
                    ('feosco_city_id', '=', rec.partner_id.feosco_city_id.id),
                    ('feosco_district_id', '=', rec.partner_id.feosco_district_id.id),
                ])
                if transport_route_ids:
                    rec.payment_address = "%s, %s, %s, %s" % (
                        rec.transport_route_id.transporter_id.address or '',
                        rec.transport_route_id.transporter_id.phuong_xa.name or '',
                        rec.transport_route_id.transporter_id.feosco_district_id.name or '',
                        rec.transport_route_id.transporter_id.feosco_city_id.name or '')

    # if self.partner_id and self.purchase_order_return:
    #         self.delivery_method = self.partner_id.delivery_method
    #         self.transport_route_id = self.partner_id.transport_route_id
    #         # delivery_scope_ids = self.env['tts.delivery.scope'].search(
    #         #     [('feosco_city_id', '=', self.partner_id.feosco_city_id.id),
    #         #      ('feosco_district_id', '=', self.partner_id.feosco_district_id.id),
    #         #      ('phuong_xa', '=', self.partner_id.feosco_ward_id.id)])
    #         # if delivery_scope_ids:
    #         #     self.delivery_scope_id = delivery_scope_ids[0]
    #         self.delivery_scope_id = self.partner_id.delivery_scope_id

    @api.onchange('location_return')
    def onchange_location_return(self):
        if self.location_return and self.location_return == 'normal':
            self.location_id = False
            return {
                'domain': {
                    'location_id': [('not_sellable', '!=', True)]
                }
            }
        elif self.location_return and self.location_return == 'damaged':
            self.location_id = False
            return {
                'domain': {
                    'location_id': [('not_sellable', '=', True)]
                }
            }

    @api.multi
    def button_draft(self):
        purchase_id = self.copy()
        self.purchase_return_id = purchase_id
        if self.purchase_order_return == False:
            action = self.env.ref('purchase.purchase_rfq')
        else:
            action = self.env.ref('sale_purchase_returns.purchase_order_return_action')
        result = action.read()[0]

        res = self.env.ref('purchase.purchase_order_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = purchase_id.id
        return result

    @api.multi
    def get_operation_state(self):
        for rec in self:
            if rec.reason_cancel:
                if rec.picking_ids and any(picking.state != 'done' for picking in
                                           rec.picking_ids.filtered(lambda line: line.is_picking_return == True)):
                    # self._cr.execute("UPDATE purchase_order SET operation_state = '%s' WHERE id = %s" %('reverse_tranfer',rec.id))
                    rec.operation_state = 'reverse_tranfer'
                else:
                    # self._cr.execute(
                    #     "UPDATE purchase_order SET operation_state = '%s' WHERE id = %s" % ('cancel',rec.id))
                    rec.operation_state = 'cancel'

            elif rec.picking_ids:
                if not rec.purchase_order_return:
                    if any(picking.state != 'done' for picking in
                           rec.picking_ids.filtered(lambda line: line.picking_type_code == 'incoming')):
                        pick_ids = rec.picking_ids.filtered(lambda line: line.picking_type_code == 'incoming')
                        if 'reveive' in pick_ids.mapped('receipt_state'):
                            # self._cr.execute(
                            #     "UPDATE purchase_order SET operation_state = '%s' WHERE id = %s" % ('reveive', rec.id))
                            rec.operation_state = 'reveive'

                    elif any(pack.state != 'done' for pack in
                             rec.picking_ids.filtered(lambda line: line.is_internal_transfer == True)):
                        pack_ids = rec.picking_ids.filtered(lambda line: line.is_internal_transfer == True)
                        # if 'checking' in pack_ids.mapped('internal_transfer_state'):
                        #     rec.operation_state = 'checking'
                        # else:
                        #     rec.operation_state = 'checking'
                        if pack_ids:
                            # self._cr.execute(
                            #     "UPDATE purchase_order SET operation_state = '%s' WHERE id = %s" % (pack_ids.mapped('internal_transfer_state')[0], rec.id))
                            rec.operation_state = pack_ids.mapped('internal_transfer_state')[0]
                    else:
                        # self._cr.execute(
                        #     "UPDATE purchase_order SET operation_state = '%s' WHERE id = %s" % ('done', rec.id))
                        rec.operation_state = 'done'
                else:
                    if any(picking.state != 'done' for picking in
                           rec.picking_ids.filtered(lambda line: line.check_is_pick == True)):
                        pick_ids = rec.picking_ids.filtered(lambda line: line.check_is_pick == True)
                        if 'waiting_pick' in pick_ids.mapped('state_pick'):
                            # self._cr.execute(
                            #     "UPDATE purchase_order SET operation_state = '%s' WHERE id = %s" % ('waiting_pick', rec.id))
                            rec.operation_state = 'waiting_pick'
                        elif 'ready_pick' in pick_ids.mapped('state_pick'):
                            # self._cr.execute(
                            #     "UPDATE purchase_order SET operation_state = '%s' WHERE id = %s" % (
                            #     'ready_pick', rec.id))
                            rec.operation_state = 'ready_pick'
                        elif 'picking' in pick_ids.mapped('state_pick'):
                            # self._cr.execute(
                            #     "UPDATE purchase_order SET operation_state = '%s' WHERE id = %s" % (
                            #         'picking', rec.id))
                            rec.operation_state = 'picking'
                    elif any(pack.state != 'done' for pack in
                             rec.picking_ids.filtered(lambda line: line.check_is_pack == True)):
                        pack_ids = rec.picking_ids.filtered(lambda line: line.check_is_pack == True)
                        if 'waiting_pack' in pack_ids.mapped('state_pack'):
                            # self._cr.execute(
                            #     "UPDATE purchase_order SET operation_state = '%s' WHERE id = %s" % (
                            #         'waiting_pack', rec.id))
                            rec.operation_state = 'waiting_pack'
                        elif 'packing' in pack_ids.mapped('state_pack'):
                            # self._cr.execute(
                            #     "UPDATE purchase_order SET operation_state = '%s' WHERE id = %s" % (
                            #         'packing', rec.id))
                            rec.operation_state = 'packing'
                    else:
                        delivery_ids = rec.picking_ids.filtered(lambda r: r.check_is_delivery == True)
                        if 'done' in delivery_ids.mapped('state_delivery'):
                            # self._cr.execute(
                            #     "UPDATE purchase_order SET operation_state = '%s' WHERE id = %s" % (
                            #         'done', rec.id))
                            rec.operation_state = 'done'
                        elif 'waiting_delivery' in delivery_ids.mapped('state_delivery'):
                            # self._cr.execute(
                            #     "UPDATE purchase_order SET operation_state = '%s' WHERE id = %s" % (
                            #         'waiting_delivery', rec.id))
                            rec.operation_state = 'waiting_delivery'
                        elif 'delivery' in delivery_ids.mapped('state_delivery'):
                            # self._cr.execute(
                            #     "UPDATE purchase_order SET operation_state = '%s' WHERE id = %s" % (
                            #         'delivery', rec.id))
                            rec.operation_state = 'delivery'

    @api.multi
    def _get_show_cancel(self):
        for order in self:
            if not order.picking_ids:
                if order.reason_cancel:
                    order.check_show_cancel = True
                else:
                    order.check_show_cancel = False
            else:
                if order.reason_cancel:
                    order.check_show_cancel = True
                else:
                    if order.purchase_order_return == False:
                        picking_ids = order.picking_ids.filtered(
                            lambda p: p.state != 'cancel' and not p.is_picking_return and not p.have_picking_return)
                        delivery_id = picking_ids.filtered(lambda l: l.is_internal_transfer == True)
                        if delivery_id and all(pick.state == 'done' for pick in delivery_id):
                            order.check_show_cancel = True
                    else:
                        order.check_show_cancel = False

    @api.depends('state')
    def get_state_return(self):
        for record in self:
            record.state_return = record.state

    @api.multi
    def action_sale_cancel(self):
        for rec in self:
            action = self.env.ref('tts_modifier_purchase_return.purchase_cancel_popup_action').read()[0]
            action['context'] = {'default_order_id': rec.id}
            return action

    def _get_picking_value(self, picking_type_id, move_line=False, location_return=False, group_id=None):
        location_id = False
        location_dest_id = False
        if picking_type_id:
            procurement_rule = self.env['procurement.rule'].search([('picking_type_id', '=', picking_type_id.id)],
                                                                   limit=1)
            location_id = procurement_rule.location_src_id
            location_dest_id = procurement_rule.location_id
        kho_luu_tru = 'normal' if self.location_return == 'normal' else 'error'
        picking_id = self.env['stock.picking'].create({
            'picking_type_id': picking_type_id.id,
            'partner_id': self.partner_id.id,
            'origin': self.name,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'check_return_picking': True,
            'min_date': self.date_order,
            'user_return_id': self.env.uid,
            'picking_note': self.notes,
            'kho_luu_tru' : kho_luu_tru
        })

        picking_line = []
        for line in self.order_line:
            if line.product_id or line.quantity != 0:
                if location_return == 'damaged':
                    qty = line.product_id.with_context(location=self.location_id.id,
                                                       location_id=self.location_id.id).qty_available
                    if qty < line.product_qty:
                        raise UserError('Không đủ hàng để trả. Chỉ có %s sản phẩm %s trong %s.' % (
                            qty, line.product_id.display_name, self.location_id.display_name))
                    picking_id.location_id = self.location_id
                    location_id = self.location_id
                elif location_return == 'normal':
                    if self.location_id == self.env.ref('stock.stock_location_stock'):
                        qty = line.product_id.sp_co_the_ban
                        if (qty + line.product_qty) < 0:
                            raise UserError('Không đủ hàng để trả. Chỉ có %s sản phẩm %s sẵn sàng trong %s.' % (
                                (qty + line.product_qty), line.product_id.display_name, self.location_id.display_name))
                    else:
                        qty_available = line.product_id.with_context(location=self.location_id.id,
                                                                     location_id=self.location_id.id).qty_available
                        sp_ban_chua_giao = line.product_id.with_context(location=self.location_id.id,
                                                                        location_id=self.location_id.id).sp_ban_chua_giao
                        if (qty_available - sp_ban_chua_giao + line.product_qty) < line.product_qty:
                            raise UserError('Không đủ hàng để trả. Chỉ có %s sản phẩm %s sẵn sàng trong %s.' % (
                                (qty_available - sp_ban_chua_giao + line.product_qty), line.product_id.display_name,
                                self.location_id.display_name))
                picking_line.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_qty,
                    'product_uom': line.product_uom.id,
                    'location_id': location_id.id,
                    'picking_type_id': picking_type_id.id,
                    'warehouse_id': picking_type_id.warehouse_id.id,
                    'location_dest_id': location_dest_id.id,
                    'name': line.product_id.display_name,
                    'purchase_line_id': line.id if not group_id else False,
                    'group_id': group_id and group_id.id,
                    'procure_method': 'make_to_stock',
                    'origin': self.name,
                    'price_unit': line.price_unit,
                    'date': self.date_order,
                    'partner_id': self.partner_id.id,
                    'move_dest_id': move_line.filtered(
                        lambda m: m.product_id == line.product_id).id if move_line else False
                }))
        picking_id.write({'move_lines': picking_line})
        return picking_id

    def button_action_return(self):
        if not self.group_id:
            group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
            self.group_id = group_id
        warehouse_id = self.picking_type_id.warehouse_id

        # create delivery
        out_type_id = warehouse_id.out_type_id
        delivery_id = self._get_picking_value(out_type_id, False, False, False)
        delivery_id.state_delivery = 'waiting_another_operation'

        # create pack
        pack_type_id = warehouse_id.pack_type_id
        pack_id = self._get_picking_value(pack_type_id, delivery_id.move_lines, False, group_id)
        pack_id.state_pack = 'waiting_another_operation'

        # create pick
        pick_type_id = warehouse_id.pick_type_id
        pick_id = self._get_picking_value(pick_type_id, pack_id.move_lines, self.location_return, group_id)
        pick_id.state_pick = 'ready_pick'
        pick_id.action_confirm()
        pick_id.action_assign()

        self.write({
            'state': 'purchase',
            'confirmation_date': datetime.today(),
            'date_approve': datetime.today(),
            'validate_date': datetime.today(),
            'validate_by': self.env.uid
        })

        return True

    @api.multi
    def update_price_move_purchase_return(self):
        picking_type_id = self.env.ref('stock.picking_type_out')
        purchase_line_ids = self.env['purchase.order.line'].search(
            [('order_id.purchase_order_return', '=', True), ('order_id.state', '=', 'purchase')])
        for purchase_line_id in purchase_line_ids:
            move_ids = self.env['stock.move'].search(
                [('origin', '=', purchase_line_id.order_id.name), ('product_id', '=', purchase_line_id.product_id.id)])
            out_move = move_ids.filtered(lambda m: m.picking_type_id == picking_type_id)
            moves = move_ids.filtered(lambda m: m.picking_type_id != picking_type_id)
            group_id = purchase_line_id.order_id.group_id
            if not group_id:
                group_id = purchase_line_id.order_id.group_id.create({
                    'name': purchase_line_id.order_id.name,
                    'partner_id': purchase_line_id.order_id.partner_id.id
                })
                purchase_line_id.order_id.group_id = group_id
            out_move.write({
                'purchase_line_id': purchase_line_id.id,
                'group_id': purchase_line_id.order_id.group_id.id
            })
            moves.write({
                'purchase_line_id': False,
                'group_id': purchase_line_id.order_id.group_id.id
            })
        default_code = ['SPV000465', 'SPV000466', 'SPV000467', 'SPV000468',
                        'SPV000474', 'SPV000479', 'SPV000480', 'SPV000481',
                        'SPV000482', 'SPV000483', 'SPV000484']
        purchase_ids = self.env['purchase.order'].browse([2220, 2055])
        for purchase in purchase_ids:
            for line in purchase.order_line:
                if line.product_id.default_code in default_code:
                    print "%s - %s" % (line.product_id.display_name, line.price_unit)

                    price_unit = line.product_id.get_history_price(line.product_id.company_id.id, line.date_order)

                    print 'update Unit price -> %s' % price_unit
                    line.price_unit = price_unit
            purchase.button_dummy()


    @api.multi
    def update_purchase_return_bill(self):
        purchase_line_ids = self.env['purchase.order.line'].search(
            [('order_id.purchase_order_return', '=', True), ('product_id.purchase_method', '!=', 'purchase')])
        purchase_ids = purchase_line_ids.mapped('order_id')
        for purchase_id in purchase_ids:
            purchase_id.with_context(active_ids=purchase_id.ids).multi_update_account_invoice()
