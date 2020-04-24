# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_round

class StockMove(models.Model):
    _inherit = 'stock.move'

    is_journal_later = fields.Boolean('Journal Later', default=False)

    @api.multi
    def create_cong_trinh_quant(self):
        for move in self:
            query = "UPDATE stock_move SET state='confirmed' WHERE id = %s" % (move.id,)
            self.env.cr.execute(query)

            move.action_assign()
            move.with_context(force_period_date=move.date).action_done()
            #
            # for quant in move.quant_ids:
            #     if quant.is_journal_later:
            #         move.is_journal_later = True
            #         break

    @api.multi
    def create_sale_quant(self):
        for move in self:
            query = "UPDATE stock_move SET state='confirmed' WHERE id = %s" % (move.id,)
            self.env.cr.execute(query)

            move.action_assign()
            move.with_context(force_period_date=move.date).action_done()

    @api.multi
    def create_production_transfer_quant(self):
        did_reset_pickings = []
        for stock_move in self:
            if stock_move.picking_id and stock_move.picking_id.pack_operation_product_ids:
                if stock_move.picking_id.id not in did_reset_pickings:
                    move_outs = self.env['stock.move'].search([
                        ('picking_id', '=', stock_move.picking_id.id),
                        ('product_id', '=', stock_move.product_id.id),
                        ('state', '=', 'done'),
                        ('location_id', '=', stock_move.location_id.id),
                        ('location_dest_id', '!=', stock_move.location_id.id),
                    ], 0, 0, 'date asc')

                    query = "UPDATE stock_move SET state='confirmed' WHERE id IN (%s)" % (','.join(str(v) for v in move_outs.ids),)
                    self.env.cr.execute(query)

                    move_outs.action_assign(True)
                    move_outs.with_context(force_period_date=stock_move.date).action_done()

                    did_reset_pickings.append(stock_move.picking_id.id)

            else:
                query = "UPDATE stock_move SET state='confirmed' WHERE id = %s" % (stock_move.id,)
                self.env.cr.execute(query)

                stock_move.action_assign(True)
                stock_move.with_context(force_period_date=stock_move.date).action_done()

    @api.multi
    def create_material_transfer_quant(self):
        for move in self:
            query = "UPDATE stock_move SET state='confirmed' WHERE id = %s" % (move.id,)
            self.env.cr.execute(query)

            move.action_assign()
            move.with_context(force_period_date=move.date).action_done()

    @api.multi
    def create_disassemble_input_quant(self):
        for move in self:
            query = "UPDATE stock_move SET state='confirmed' WHERE id = %s" % (move.id,)
            self.env.cr.execute(query)

            move.action_assign()
            move.with_context(force_period_date=move.date).action_done()

    @api.multi
    def create_purchase_return_quant(self):
        for move in self:
            query = "UPDATE stock_move SET state='confirmed' WHERE id = %s" % (move.id,)
            self.env.cr.execute(query)

            move.action_assign()
            move.with_context(force_period_date=move.date).action_done()

    @api.multi
    def create_inventory_decrease_quant(self):
        for move in self:
            query = "UPDATE stock_move SET state='confirmed' WHERE id = %s" % (move.id,)
            self.env.cr.execute(query)

            move.action_assign()
            move.with_context(force_period_date=move.date).action_done()

    @api.multi
    def create_disassemble_output_quant(self):
        for move in self:
            move.quick_create_stock_quant()
            move.with_context(force_period_date=move.date).quick_create_journal_entry()

    @api.multi
    def create_material_return_quant(self):
        for move in self:
            move.quick_create_stock_quant()
            move.with_context(force_period_date=move.date).quick_create_journal_entry()

    @api.multi
    def create_sale_return_quant(self):
        for move in self:
            move.quick_create_stock_quant()
            move.with_context(force_period_date=move.date).quick_create_journal_entry()

    @api.multi
    def create_mrp_quant(self):
        for move in self:
            # production = move.production_id
            # production.set_to_draft_mp()
            # if production.state == 'confirmed':
            #     production.multi_confirm_production()
            move.quick_create_stock_quant()
            move.with_context(force_period_date=move.date).quick_create_journal_entry()

    @api.multi
    def create_purchase_quant(self):
        for move in self:
            move.quick_create_stock_quant()
            move.with_context(force_period_date=move.date).quick_create_journal_entry()

    @api.multi
    def create_inventory_inscrease_quant(self):
        for move in self:
            move.quick_create_stock_quant()
            move.with_context(force_period_date=self.date).quick_create_journal_entry()

    @api.multi
    def get_price_unit(self):
        price_unit = super(StockMove, self).get_price_unit()
        # if not price_unit and self.production_id:
        #     price_unit = 1
        return price_unit

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        self.ensure_one()

        result = []
        if not self.env.context.get('from_stock_account', False):
            result = super(StockMove, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
            if self.production_id:
                item_index = 0
                for item in result:
                    if len(item) == 3:
                        if not item[2].get('ref', False):
                            result[item_index][2].update({
                                'ref': self.production_id.name,
                            })
                    item_index += 1
            elif self.inventory_id:
                item_index = 0
                for item in result:
                    if len(item) == 3:
                        if not item[2].get('ref', False):
                            result[item_index][2].update({
                                'ref': self.inventory_id.name,
                            })
                    item_index += 1
        return result

    @api.multi
    def quick_create_journal_entry(self):
        for move in self:
            for quant in move.quant_ids:
                quant._account_entry_move(move)

    @api.multi
    def quick_create_stock_quant(self):
        Quant = self.env['stock.quant']

        for move in self:
            if float_compare(move.product_uom_qty, 0, precision_rounding=move.product_id.uom_id.rounding) > 0:  # In case no pack operations in picking
                # move.check_tracking(False)  # TDE: do in batch ? redone ? check this

                preferred_domain_list = [
                    [('reservation_id', '=', move.id)],
                    [('reservation_id', '=', False)],
                    [
                        '&',
                        ('reservation_id', '!=', move.id),
                        ('reservation_id', '!=', False)
                    ]
                ]

                quants = Quant.quants_get_preferred_domain(
                    move.product_uom_qty, move, domain=[('qty', '>', 0)],
                    preferred_domain_list=preferred_domain_list)

                Quant.quants_move(
                    quants, move.with_context(from_stock_account=True), move.location_dest_id,
                    lot_id=move.restrict_lot_id.id, owner_id=move.restrict_partner_id.id)

                # unreserve the quants and make them available for other operations/moves
                move.quants_unreserve()