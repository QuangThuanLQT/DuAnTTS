# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    def get_price_full(self):
        price_unit = 0
        if self.production_id.move_finished_ids:
            self.production_id.with_context(get_price_unit=True).compute_amount_product()
            new_cost = self.production_id.material_cost + sum(self.production_id.account_move_ids.mapped('debit'))
            qty_total = sum(self.production_id.move_finished_ids.mapped('product_uom_qty'))
            price_unit = new_cost / (qty_total or 1)
        return price_unit

    def get_price_unit(self):
        """ Returns the unit price to store on the quant """
        if self.production_id:
            return self.get_price_full()
        else:
            return super(StockMove, self).get_price_unit()

    @api.multi
    def set_to_draft_stm(self):
        picking_to_confirm = []
        # Cancel stock move done state from do_reset_stock_picking function
        for stock_move in self:
            move_location_id = stock_move.location_id
            move_location_dest_id = stock_move.location_dest_id
            for stock_quant in stock_move.quant_ids:
                # unreserve picking that related to current quant
                if stock_quant.reservation_id and stock_quant.reservation_id.id:
                    stock_quant.reservation_id.picking_id.do_unreserve()

                # TODO: Reset other picking first
                for history in stock_quant.history_ids:
                    # TODO: Check newer transaction by date
                    # Check newer than current stock move
                    if history.date > stock_move.date:  # TODO: Seem have problem here.
                        # Step 1: Reset to draft
                        history.picking_id.do_reset_stock_picking()
                        # Step 2: Record into to confirm list
                        if history.picking_id.id != stock_move.picking_id.id:
                            picking_to_confirm.append(history.picking_id)

                # TODO: Reset current stock move
                for history in stock_quant.history_ids:
                    if history.id == stock_move.id:

                        in_date = False
                        # Step 2.1 - Update history
                        history_ids = []
                        for history in stock_quant.history_ids:
                            if history.date < stock_move.date:
                                history_ids.append(history.id)
                                in_date = history.date

                        # Step 2.2 - Ready to cancel
                        if len(history_ids) > 0:
                            quant_data = {
                                'history_ids': [(6, 0, history_ids)],
                                'in_date': in_date or stock_quant.in_date,
                                'location_id': move_location_id and move_location_id.id or stock_quant.location_id.id,
                            }
                            stock_quant.write(quant_data)
                        else:
                            stock_quant.with_context({'force_unlink': True}).unlink()

        # Step 3: Reset stock move status to draft
        for stock_move in self:
            stock_move.state = 'draft'

    @api.multi
    def check_procure_method_available(self):
        # TODO: Fixed the stock
        # return True

        stock_location = self.env.ref('stock.stock_location_stock')
        ksx_location   = self.env.ref('cptuanhuy_mrp.location_ksx_stock')

        for record in self:
            if record.procure_method == 'make_to_order':
                quantity_available = 0
                if record.location_id.id in [stock_location.id, ksx_location.id]:
                    quants = self.env['stock.quant'].search([
                        ('location_id', '=', record.location_id.id),
                        ('reservation_id', '=', False),
                        ('product_id', '=', record.product_id.id),
                    ])
                    for quant in quants:
                        quantity_available += quant.qty

                if quantity_available >= record.product_uom_qty:
                    record.procure_method = 'make_to_stock'
    @api.multi
    def action_assign(self, no_prepare=False):
        self.check_procure_method_available()

        res = super(StockMove, self).action_assign(no_prepare)
        return res

    @api.multi
    def action_confirm(self):
        self.check_procure_method_available()

        res = super(StockMove, self).action_confirm()
        return res