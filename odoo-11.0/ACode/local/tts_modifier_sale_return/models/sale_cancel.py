# -*- coding: utf-8 -*-

from odoo import models, fields, api

class sale_cancel_popup(models.Model):
    _name = 'sale.cancel.popup'

    name = fields.Many2one('reason.cancel.sale', string='Lý do')
    order_id = fields.Many2one('sale.order')

    def cancel_account_voucher(self, order_id):
        voucher_line_ids = self.env['voucher.sale.line'].search([('order_id', '=', order_id.id),('check', '=', True)])
        voucher_ids = voucher_line_ids.mapped('account_voucher_id')
        for voucher_id in voucher_ids:
            voucher_id.with_context({'cancel_sale' : True}).cancel_voucher()

    @api.multi
    def action_cancel(self):
        if self.order_id and not self.order_id.sale_order_return:
            self.cancel_account_voucher(self.order_id)
            self.order_id.reason_cancel = self.name
            if not self.order_id.picking_ids:
                self.order_id.state = 'cancel'
                self.order_id.trang_thai_dh = 'cancel'
            else:
                picking_ids = self.order_id.picking_ids.filtered(lambda p: p.state != 'cancel' and not p.is_picking_return and not p.have_picking_return)
                picking_pick = picking_ids.filtered(lambda l: l.check_is_pick == True)
                picking_pack = picking_ids.filtered(lambda l: l.check_is_pack == True)
                picking_out = picking_ids.filtered(lambda l: l.check_is_delivery == True)
                if picking_pick and all(pick.state != 'done' for pick in picking_pick):
                    #cancel all picking
                    picking_pick.action_cancel()
                    picking_pick.state_pick = 'cancel'
                    picking_pack.action_cancel()
                    picking_pack.state_pack = 'cancel'
                    picking_out.action_cancel()
                    picking_out.state_delivery = 'cancel'
                    self.order_id.state = 'cancel'
                elif picking_pick and any(pick.state == 'done' for pick in picking_pick):
                    for pick in picking_pick:
                        if pick.state == 'done':
                            if all(move.state != 'done' for move in pick.move_lines.mapped('move_dest_id')):
                                # pick_obj = self.env['stock.return.picking'].with_context(active_id = pick.id)
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
                    else:
                        picking_pack.action_cancel()
                        picking_pack.state_pack = 'cancel'
                        picking_out.action_cancel()
                        picking_out.state_delivery = 'cancel'

        elif self.order_id and self.order_id.sale_order_return:
            self.order_id.sale_return_cancel = True
            self.order_id.reason_cancel = self.name
            if not self.order_id.picking_ids:
                self.order_id.state = 'cancel'
            else:
                picking_ids = self.order_id.picking_ids.filtered(lambda p: p.state != 'cancel')
                receipt_id = picking_ids.filtered(lambda l: l.picking_type_code == 'incoming')
                interl_id = picking_ids.filtered(lambda l: l.picking_type_code == 'internal' and l.is_internal_transfer)
                if receipt_id and receipt_id.state != 'done':
                    # cancel all picking
                    receipt_id.action_cancel()
                    receipt_id.receipt_state = 'cancel'
                    interl_id.action_cancel()
                    interl_id.internal_transfer_state = 'cancel'
                    self.order_id.state = 'cancel'
                elif receipt_id and receipt_id.state == 'done':
                    if interl_id and interl_id.state != 'done':
                        # Return picking pick
                        # pick_obj = self.env['stock.return.picking'].with_context({'active_id': receipt_id.id})
                        # pick_return_data = pick_obj.sudo().default_get(pick_obj._fields)
                        # pick_return = pick_obj.create(pick_return_data)
                        # pick_return.create_returns()
                        # Cancel picking pack and picking out
                        receipt_id.create_picking_return()
                        interl_id.action_cancel()
                        interl_id.internal_transfer_state = 'cancel'



class reason_cancel_sale(models.Model):
    _name = 'reason.cancel.sale'

    name = fields.Char(string='Lý do')