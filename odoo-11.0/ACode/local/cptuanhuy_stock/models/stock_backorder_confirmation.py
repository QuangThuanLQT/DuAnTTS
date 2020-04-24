# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    @api.one
    def _process(self, cancel_backorder=False):
        operations_to_delete = self.pick_id.pack_operation_ids.filtered(lambda o: o.qty_done <= 0)
        for pack in self.pick_id.pack_operation_ids - operations_to_delete:
            pack.product_qty = pack.qty_done
        operations_to_delete.unlink()
        self.pick_id.do_transfer()
        if cancel_backorder:
            backorder_pick_ids = self.env['stock.picking'].search([('backorder_id', '=', self.pick_id.id)])
            backorder_pick_ids.action_cancel()
            for backorder_pick in backorder_pick_ids:
                self.pick_id.message_post(body=_("Back order <em>%s</em> <b>cancelled</b>.") % (backorder_pick.name))
        # res = super(StockBackorderConfirmation, self)._process(cancel_backorder=cancel_backorder)
        backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', self.pick_id.id)])
        stock_in = self.get_stock_in(self.pick_id)
        if stock_in and backorder_pick:
            # TODO: Need to double check
            self.env['stock.picking'].browse(stock_in).write({'stock_out_ids': [(6, 0, backorder_pick.ids)]})
        # return res

    def get_stock_in(self, picking):
        if not picking.backorder_id:
            sql = """SELECT incoming_id FROM stock_out_picking_rel WHERE stock_out_id = %s""" %(picking.id)
            self.env.cr.execute(sql)
            stock_id = self.env.cr.fetchall()
            if stock_id and stock_id[0]:
                return stock_id[0][0]
            else:
                return False
        else:
            return self.get_stock_in(picking.backorder_id)
