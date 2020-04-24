# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    @api.multi
    def _create_returns(self):
        new_picking_id, pick_type_id = super(StockReturnPicking, self)._create_returns()
        new_picking = self.env['stock.picking'].browse([new_picking_id])
        for move in new_picking.move_lines:
            return_picking_line = self.product_return_moves.filtered(lambda r: r.move_id == move.origin_returned_move_id)
            if return_picking_line and return_picking_line.move_id.purchase_line_id:
                move.purchase_line_id = return_picking_line.move_id.purchase_line_id

        return new_picking_id, pick_type_id
