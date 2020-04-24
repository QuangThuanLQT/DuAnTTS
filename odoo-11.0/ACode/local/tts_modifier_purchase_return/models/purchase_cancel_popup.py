# -*- coding: utf-8 -*-

from odoo import models, fields, api

class reason_cancel_purchase(models.Model):
    _name = 'reason.cancel.purchase'

    name = fields.Char(string='Lý do')


class purchase_cancel_popup(models.TransientModel):
    _name = 'purchase.cancel.popup'

    name = fields.Many2one('reason.cancel.purchase', string='Lý do')
    order_id = fields.Many2one('purchase.order')

    @api.multi
    def action_cancel(self):
        if self.order_id:
            self.order_id.reason_cancel = self.name
            if self.order_id.purchase_order_return == False:
                if self.order_id.picking_ids:
                    picking_ids = self.order_id.picking_ids.filtered(lambda p: p.state != 'cancel' and not p.is_picking_return)
                    receipt_id = picking_ids.filtered(lambda l: l.picking_type_code == 'incoming')
                    interl_id = picking_ids.filtered(lambda l: l.picking_type_code == 'internal' and l.is_internal_transfer)
                    if receipt_id and receipt_id.state != 'done':
                        #cancel all picking
                        receipt_id.action_cancel()
                        receipt_id.purchase_reason_cancel = self.name
                        receipt_id.receipt_state = 'cancel'
                        interl_id.action_cancel()
                        interl_id.purchase_reason_cancel = self.name
                        interl_id.internal_transfer_state = 'cancel'
                        self.order_id.state = 'cancel'
                    elif receipt_id and receipt_id.state == 'done':
                        if interl_id and interl_id.state != 'done':
                            # Return picking pick
                            # pick_obj = self.env['stock.return.picking'].with_context({'active_id' : receipt_id.id})
                            # pick_return_data = pick_obj.sudo().default_get(pick_obj._fields)
                            # pick_return = pick_obj.create(pick_return_data)
                            # pick_return.create_returns()
                            receipt_id.create_picking_return()
                            # Cancel picking pack and picking out
                            interl_id.action_cancel()
                            interl_id.purchase_reason_cancel = self.name
                            interl_id.internal_transfer_state = 'cancel'
                else:
                    self.order_id.state = 'cancel'
                    self.order_id.operation_state = 'cancel'
            else:
                self.order_id.state = 'cancel'
                self.order_id.operation_state = 'cancel'
                self.order_id.reason_cancel = self.name
                picking_ids = self.order_id.picking_ids.filtered(
                    lambda p: p.state != 'cancel' and not p.is_picking_return and not p.have_picking_return)
                picking_pick = picking_ids.filtered(lambda l: l.check_is_pick == True)
                picking_pack = picking_ids.filtered(lambda l: l.check_is_pack == True)
                picking_out = picking_ids.filtered(lambda l: l.check_is_delivery == True)
                if picking_pick and all(pick.state != 'done' for pick in picking_pick):
                    # cancel all picking
                    if picking_pick:
                        picking_pick.action_cancel()
                        picking_pick.state_pick = 'cancel'
                    if picking_pack:
                        picking_pack.action_cancel()
                        picking_pack.state_pack = 'cancel'
                    if picking_out:
                        picking_out.action_cancel()
                        picking_out.state_delivery = 'cancel'
                    self.order_id.state = 'cancel'
                elif picking_pick and any(pick.state == 'done' for pick in picking_pick):
                    for pick in picking_pick:
                        if pick.state == 'done':
                            if all(move.state != 'done' for move in pick.move_lines.mapped('move_dest_id')):
                                # pick_obj = self.env['stock.return.picking'].with_context(active_id=pick.id)
                                # pick_return_data = pick_obj.sudo().default_get(pick_obj._fields)
                                # pick_return = pick_obj.create(pick_return_data)
                                # pick_return.create_returns()
                                pick.create_picking_return()
                        else:
                            pick.action_cancel()
                            pick.state_pick = 'cancel'
                    if picking_pack and any(pack.state == 'done' for pack in picking_pack):
                        for pack in picking_pack:
                            if pack.state == 'done':
                                if all(move.state != 'done' for move in pack.move_lines.mapped('move_dest_id')):
                                    # pack_obj = self.env['stock.return.picking'].with_context({'active_id': pack.id})
                                    # pack_return_data = pack_obj.sudo().default_get(pack_obj._fields)
                                    # pack_return = pack_obj.create(pack_return_data)
                                    # pack_return.create_returns()
                                    pack.create_picking_return()
                            else:
                                pack.action_cancel()
                                pack.state_pack = 'cancel'
                        picking_out.action_cancel()
                        picking_out.state_delivery = 'cancel'
                        True
                    else:
                        picking_pack.action_cancel()
                        picking_pack.state_pack = 'cancel'
                        picking_out.action_cancel()
                        picking_out.state_delivery = 'cancel'

