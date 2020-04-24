# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class sale_order(models.Model):
    _inherit = 'sale.order'

    sale_method = fields.Selection([('customer', 'Bán cho Khách Hàng'), ('warehouse', 'Bán cho Kho')],
                                   default='customer', string='Route')

    @api.model
    def _cron_queue_create_picking(self):
        sales = self.search([
            ('queue_procurement', '=', True),
            ('state', '=', 'sale'),
        ])

        if len(sales) > 0:
            for sale in sales:
                sale.create_picking_tts()

            sales.write({
                'queue_procurement': False
            })

        return True

    

    @api.multi
    def action_confirm_order(self):
        res = super(sale_order, self).action_confirm_order()
        if self.quy_trinh_ban_hang == 'print':
            self._create_picking_print()
            self.queue_procurement = False
        return res

    def check_produce_image(self, picking_image):
        check = False
        for line in self.thong_tin_its:
            if line.in_hinh == True:
                check = True
        if not check:
            picking_image.state = 'done'
            picking_image.produce_image_state = 'done'
            picking_image.produce_image_state_default = 'done'
        return True

    @api.multi
    def write(self, vals):
        res = super(sale_order, self).write(vals)
        if vals.get('payment_method', False):
            for order in self:
                if order.payment_method.type == 'cash':
                    product_name_ids = order.picking_ids.filtered(lambda x: x.check_produce_name)
                    for pick in product_name_ids:
                        if pick.produce_name_state in ('draft', 'waiting_produce', 'ready_produce'):
                            pick.write({
                                'state': 'assigned',
                                'produce_name_state': 'ready_produce',
                            })
                    product_image_ids = order.picking_ids.filtered(lambda x: x.check_produce_image)
                    for pick in product_image_ids:
                        if pick.produce_image_state in ('draft', 'waiting_produce'):
                            pick.write({
                                'state': 'assigned',
                                'produce_image_state': 'ready_produce',
                            })
                elif order.payment_method.type == 'bank':
                    product_name_ids = order.picking_ids.filtered(lambda x: x.check_produce_name)
                    for pick in product_name_ids:
                        if pick.produce_name_state in ('ready_produce'):
                            pick.write({
                                'state': 'confirmed',
                                'produce_name_state': 'waiting_produce',
                            })
                    product_image_ids = order.picking_ids.filtered(lambda x: x.check_produce_image)
                    for pick in product_image_ids:
                        if pick.produce_image_state in ('ready_produce'):
                            pick.write({
                                'state': 'confirmed',
                                'produce_image_state': 'waiting_produce',
                            })
        return res

    def _generation_move_line(self, line, picking_type_id, location_id, location_dest_id, move_line):
        return {
            'product_id': line.product_id.id,
            'product_uom_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'location_id': location_id,
            'picking_type_id': picking_type_id.id,
            'warehouse_id': picking_type_id.warehouse_id.id,
            'location_dest_id': location_dest_id,
            'name': self.name,
            'procure_method': 'make_to_stock',
            'origin': self.name,
            'price_unit': line.price_unit * (1 - (line.discount or 0.0) / 100.0) or 0,
            'date': self.date_order,
            'group_id': line.order_id.procurement_group_id.id,
            'print_qty': line.print_qty,
            'partner_id': self.partner_id.id,
            'move_dest_id': move_line.filtered(
                lambda m: m.product_id == line.product_id).id if move_line else False
        }

    def _get_picking_value(self, picking_type_id, move_line=False, location_return=None, null_location=None):

        location_id = False
        location_dest_id = False
        if picking_type_id:
            if not null_location:
                if picking_type_id.default_location_src_id:
                    location_id = picking_type_id.default_location_src_id.id
                elif self.partner_id:
                    location_id = self.partner_id.property_stock_supplier.id
                else:
                    customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()

                if picking_type_id.default_location_dest_id:
                    location_dest_id = picking_type_id.default_location_dest_id.id
                elif self.partner_id:
                    location_dest_id = self.partner_id.property_stock_customer.id
                else:
                    location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()
        if picking_type_id.picking_type == 'pick':
            location_dest_id = picking_type_id.warehouse_id.wh_kcs1_stock_loc_id.id
        if picking_type_id.picking_type == 'pack':
            procurement_rule = self.env['procurement.rule'].search([('picking_type_id', '=', picking_type_id.id)],
                                                                   limit=1)
            location_dest_id = procurement_rule.location_id.id

        picking_id = self.env['stock.picking'].create({
            'picking_type_id': picking_type_id.id,
            'partner_id': self.partner_id.id,
            'origin': self.name,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'check_return_picking': False,
            'min_date': self.date_order,
            'picking_note': self.note,
        })

        picking_line = []

        for line in self.order_line:
            if not line.order_id.procurement_group_id:
                vals = line.order_id._prepare_procurement_group()
                line.order_id.procurement_group_id = self.env["procurement.group"].create(vals)
            if line.product_id or line.quantity != 0:
                move_data = self._generation_move_line(line, picking_type_id, location_id, location_dest_id, move_line)
                picking_line.append((0, 0, move_data))

        picking_id.write({'move_lines': picking_line})
        return picking_id

    def _create_picking_print(self):
        warehouse_id = self.warehouse_id

        # create delivery
        out_type_id = warehouse_id.out_type_id
        delivery_id = self._get_picking_value(out_type_id)
        delivery_id.state_delivery = 'waiting_another_operation'
        delivery_id.state_delivery_default = 'waiting_another_operation'
        delivery_id.action_confirm()

        # create pack
        pack_type_id = warehouse_id.pack_type_id
        pack_id = self._get_picking_value(pack_type_id, delivery_id.move_lines)
        pack_id.state_pack = 'waiting_another_operation'
        pack_id.state_pack_default = 'waiting_another_operation'
        pack_id.action_confirm()

        # create kcs2
        kcs2_type_id = warehouse_id.kcs2_type_id
        kcs2_id = self._get_picking_value(kcs2_type_id, pack_id.move_lines)
        kcs2_id.kcs2_state = 'waiting'
        kcs2_id.kcs2_state_default = 'waiting'
        kcs2_id.action_confirm()

        # create print
        print_type_id = warehouse_id.print_type_id
        print_id = self._get_picking_value(print_type_id, kcs2_id.move_lines)
        print_id.print_state = 'waiting_print'
        print_id.print_state_default = 'waiting_print'
        print_id.action_confirm()

        # create kcs1
        kcs1_type_id = warehouse_id.kcs1_type_id
        kcs1_id = self._get_picking_value(kcs1_type_id, print_id.move_lines)
        kcs1_id.kcs1_state = 'waiting'
        kcs1_id.kcs1_state_default = 'waiting'
        kcs1_id.action_confirm()

        # create product_image
        produce_image_type_id = warehouse_id.produce_image_type_id
        product_image = self._get_picking_value(produce_image_type_id, null_location=True)
        # product_image.action_confirm()
        if self.payment_method.type == 'bank':
            product_image.produce_image_state = 'waiting_produce'
            product_image.state = 'confirmed'
            product_image.produce_image_state_default = 'waiting_produce'
        elif self.payment_method.type == 'cash':
            product_image.produce_image_state = 'ready_produce'
            product_image.produce_image_state_default = 'ready_produce'
            product_image.state = 'assigned'
        self.check_produce_image(product_image)

        # create product_name
        produce_name_type_id = warehouse_id.produce_name_type_id
        product_name = self._get_picking_value(produce_name_type_id, null_location=True)
        # product_name.action_confirm()
        if self.payment_method.type == 'bank':
            product_name.produce_name_state = 'waiting_produce'
            product_name.produce_name_state_default = 'waiting_produce'
            product_name.state = 'confirmed'
        elif self.payment_method.type == 'cash':
            product_name.produce_name_state = 'ready_produce'
            product_name.produce_name_state_default = 'ready_produce'
            product_name.state = 'assigned'

        # create pick
        pick_type_id = warehouse_id.pick_type_id
        pick_id = self._get_picking_value(pick_type_id, kcs1_id.move_lines)
        if self.payment_method.type == 'bank':
            pick_id.state_pick = 'waiting_pick'
            pick_id.state_pick_default = 'waiting_pick'
        elif self.payment_method.type == 'cash':
            pick_id.state_pick = 'ready_pick'
            pick_id.state_pick_default = 'ready_pick'

        pick_id.action_confirm()
        pick_id.action_assign()
        self.write({
            'queue_procurement': False
        })
        return True

    @api.multi
    def _get_show_cancel(self):
        for order in self:
            if not order.sale_order_return:
                order.check_show_cancel = False
                if not order.picking_ids:
                    if order.reason_cancel:
                        order.check_show_cancel = True
                    else:
                        order.check_show_cancel = False
                else:
                    if order.reason_cancel:
                        order.check_show_cancel = True
                    else:
                        picking_ids = order.picking_ids.filtered(
                            lambda p: p.state != 'cancel' and not p.is_picking_return and not p.have_picking_return)
                        delivery_id = picking_ids.filtered(lambda l: l.check_is_delivery == True)
                        if delivery_id and all(pick.state == 'done' for pick in delivery_id):
                            order.check_show_cancel = True
                        picking_ids = order.picking_ids.filtered(lambda p: p.state != 'cancel')
                        interl_id = picking_ids.filtered(lambda l: l.is_internal_transfer)
                        if interl_id and all(pick.state == 'done' for pick in interl_id):
                            order.check_show_cancel = True

                        pick_id = picking_ids.filtered(lambda a: a.check_is_pick == True)
                        product_name_id = picking_ids.filtered(lambda a: a.check_produce_name == True)
                        product_image_id = picking_ids.filtered(lambda a: a.check_produce_image == True)
                        kcs1_id = picking_ids.filtered(lambda a: a.check_kcs1 == True)
                        print_id = picking_ids.filtered(lambda a: a.check_print == True)
                        kcs2_id = picking_ids.filtered(lambda a: a.check_kcs2 == True)
                        pack_id = picking_ids.filtered(lambda a: a.check_is_pack == True)

                        if order.quy_trinh_ban_hang == 'print':
                            if pick_id.mapped('state_pick') != pick_id.mapped('state_pick_default'):
                                order.check_show_cancel = True
                            if product_name_id.mapped('produce_name_state') != product_name_id.mapped(
                                    'produce_name_state_default'):
                                order.check_show_cancel = True
                            if product_image_id.mapped('produce_image_state') != product_image_id.mapped(
                                    'produce_image_state_default'):
                                order.check_show_cancel = True
                            if kcs1_id.mapped('kcs1_state') != kcs1_id.mapped('kcs1_state_default'):
                                order.check_show_cancel = True
                            if print_id.mapped('print_state') != print_id.mapped('print_state_default'):
                                order.check_show_cancel = True
                            if kcs2_id.mapped('kcs2_state') != kcs2_id.mapped('kcs2_state_default'):
                                order.check_show_cancel = True
                            if pack_id.mapped('state_pack') != pack_id.mapped('state_pack_default'):
                                order.check_show_cancel = True
                            if delivery_id.mapped('state_delivery') != delivery_id.mapped('state_delivery_default'):
                                order.check_show_cancel = True
            else:
                order.check_show_cancel = False
                if not order.picking_ids:
                    if order.reason_cancel:
                        order.check_show_cancel = True
                    else:
                        order.check_show_cancel = False
                else:
                    picking_ids = order.picking_ids.filtered(
                        lambda p: p.state != 'cancel' and not p.is_picking_return and not p.have_picking_return)
                    delivery_id = picking_ids.filtered(lambda l: l.check_is_delivery == True)
                    if delivery_id and all(pick.state == 'done' for pick in delivery_id):
                        order.check_show_cancel = True
                    picking_ids = order.picking_ids.filtered(lambda p: p.state != 'cancel')
                    interl_id = picking_ids.filtered(lambda l: l.is_internal_transfer)
                    if interl_id and all(pick.state == 'done' for pick in interl_id):
                        order.check_show_cancel = True

    def _get_picking_value_tts(self, picking_type_id):
        res = super(sale_order, self)._get_picking_value_tts(picking_type_id)
        res.picking_note = self.note
        return res
