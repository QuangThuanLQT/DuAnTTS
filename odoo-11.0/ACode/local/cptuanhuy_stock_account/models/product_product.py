# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round
_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    journal_entry_count = fields.Integer('# Journal Entry', compute='_compute_journal_entry_count')

    @api.multi
    def _compute_journal_entry_count(self):
        for product in self:
            journal_entry_count = self.env['account.move.line'].search([
                ('product_id', '=', product.id)
            ], count=True)
            product.journal_entry_count = journal_entry_count

    @api.multi
    def action_view_journal_entry(self):
        action = self.env.ref('cptuanhuy_accounting.account_move_pnl_report_action').read()[0]
        template_ids = self.mapped('product_tmpl_id').ids
        # bom specific to this variant or global to template
        action['context'] = {
            'default_product_tmpl_id': template_ids[0],
            'default_product_id': self.ids[0],
            'search_default_632': True,
            'search_default_511': True,
            'search_default_641': True,
            'search_default_642': True,
            'search_default_811': True,
            'search_default_622': True,
            'search_default_627': True,
        }
        action['domain'] = [('product_id', 'in', [self.ids])]
        return action


    @api.multi
    def update_sale_return_price(self):
        # TODO: Need to update this
        pass

    @api.multi
    def update_mrp_price(self):
        # TODO: Need to update this
        pass
        # productions = self.env['mrp.production'].search([
        #     ('state', '=', 'done')
        # ])
        # for production in productions:
        #     production.update_production_price()

    @api.multi
    def update_marerial_return_price(self):
        # TODO: Need to update this
        pass

    @api.multi
    def update_disassemble_price(self):
        # TODO: Check price later
        pass
        # for product in self:
        #     disassembles = self.env['res.disassemble'].search([
        #         ('product_id', 'in', product.product_tmpl_id.id),
        #         ('state', '=', 'done')
        #     ], order='date_disassemble ASC')
        #     for disassemble in disassembles:
        #         # TODO: Only need to checking the value now, should do update price later
        #         cost_price = 0
        #         transfered_qty = 0
        #         for quant in disassemble.move_id.quant_ids:
        #             cost_price += quant.inventory_value
        #             transfered_qty += quant.qty
        #
        #         if disassemble.quantity_pro > transfered_qty:
        #             raise Exception('Quantity greater than the reserved quantity (%s)' % transfered_qty)
        #
        #         # increasing material qty
        #         material_cost_price = 0
        #         for material in disassemble.material_id:
        #             if material.qty_pro > 0:
        #                 material_cost_price += material.cost_price
        #
        #         if float_compare(material_cost_price, cost_price, 0) != 0:
        #             raise Exception('You need to fully allocate cost to product %s' %(disassemble.name))

    @api.model
    def api_calculate_cost_price(self, product_id):
        product = self.browse(product_id)
        if product.type == 'product':
            product.calculate_cost_price()
        else:
            # Clear stock data for service product
            query = "DELETE FROM stock_quant WHERE product_id = %s" % (product.id,)
            self.env.cr.execute(query)

            query = "DELETE FROM stock_move WHERE product_id = %s" % (product.id,)
            self.env.cr.execute(query)

            query = "SELECT DISTINCT aml.move_id FROM account_move_line aml INNER JOIN account_move am ON am.id = aml.move_id WHERE aml.product_id = %s AND am.journal_id = %s" % (product.id, 7,)
            query_result = self.env['tuanhuy.base'].execute_query(query, True)
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    account_move_id = query_line[0]

                    query = "DELETE FROM account_move_line WHERE move_id = %s" % (account_move_id,)
                    self.env.cr.execute(query)

                    query = "DELETE FROM account_move WHERE id = %s" % (account_move_id,)
                    self.env.cr.execute(query)

        return True

    @api.multi
    def calculate_cost_price(self):
        stock_journal_id    = 7  # Stock journal
        stock_location      = self.env.ref('stock.stock_location_stock')
        supplier_location   = self.env.ref('stock.stock_location_suppliers')
        production_location = self.env.ref('stock.location_production')
        customer_location   = self.env.ref('stock.stock_location_customers')
        ksx_location        = self.env.ref('cptuanhuy_mrp.location_ksx_stock')
        inventory_location  = self.env.ref('stock.location_inventory')

        for product in self:
            stock_move_done_before = self.env['stock.move'].search([
                ('product_id', '=', product.id),
                ('state', '=', 'done'),
            ], count=True)

            account_move_done_before = self.env['account.move.line'].search([
                ('product_id', '=', product.id),
            ], count=True)

            inventory_moves = self.env['stock.move'].search([
                ('product_id', '=', product.id),
                ('state', '=', 'done'),
                ('inventory_id', '!=', False),
                ('location_dest_id', '=', stock_location.id),
                ('location_id', '=', inventory_location.id),
                '|',
                ('price_unit', '=', False),
                ('price_unit', '<=', 0),
            ], 0, 0, 'date asc')
            for inventory_move in inventory_moves:
                total_qty   = 0
                total_value = 0
                for inventory_quant in inventory_move.quant_ids:
                    total_qty   += inventory_quant['qty']
                    total_value += inventory_quant['inventory_value']

                if total_qty > 0:
                    price_unit = total_value / total_qty
                    query = "UPDATE stock_move SET price_unit = %s WHERE id = %s" % (price_unit, inventory_move.id,)
                    self.env.cr.execute(query)

            query = "DELETE FROM stock_quant WHERE product_id = %s" % (product.id,)
            self.env.cr.execute(query)

            query = "SELECT DISTINCT aml.move_id FROM account_move_line aml INNER JOIN account_move am ON am.id = aml.move_id WHERE aml.product_id = %s AND am.journal_id = %s" % (product.id, stock_journal_id,)
            query_result = self.env['tuanhuy.base'].execute_query(query, True)
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    account_move_id = query_line[0]

                    query = "DELETE FROM account_move_line WHERE move_id = %s" % (account_move_id,)
                    self.env.cr.execute(query)

                    query = "DELETE FROM account_move WHERE id = %s" % (account_move_id,)
                    self.env.cr.execute(query)

            # STEP1: Inventory Increase
            stock_move_ins = self.env['stock.move'].search([
                ('product_id', '=', product.id),
                ('state', '=', 'done'),
                ('inventory_id', '!=', False),
                ('location_dest_id', '=', stock_location.id),
                ('location_id', '=', inventory_location.id),
            ], 0, 0, 'date asc')
            for stock_move in stock_move_ins:
                stock_move.create_inventory_inscrease_quant()

            # STEP2: Purchase Increase
            stock_move_ins = self.env['stock.move'].search([
                ('product_id', '=', product.id),
                ('state', '=', 'done'),
                ('location_dest_id', '=', stock_location.id),
                ('location_id', '=', supplier_location.id),
            ], 0, 0, 'date asc')
            for stock_move in stock_move_ins:
                stock_move.create_purchase_quant()

            # STEP3: Sale Return Increase
            stock_move_ins = self.env['stock.move'].search([
                ('product_id', '=', product.id),
                ('state', '=', 'done'),
                ('location_dest_id', '=', stock_location.id),
                ('location_id', '=', customer_location.id),
            ], 0, 0, 'date asc')
            for stock_move in stock_move_ins:
                stock_move.create_sale_return_quant()

            # STEP4: MRP Increase
            productions = self.env['mrp.production'].search([
                ('product_id', '=', product.id),
                ('state','=','done')
            ])
            for production in productions:
                for stock_move in production.move_finished_ids:
                    stock_move.create_mrp_quant()

            # STEP5: Production Transfer
            stock_move_ins = self.env['stock.move'].search([
                ('product_id', '=', product.id),
                ('state', '=', 'done'),
                ('location_dest_id', '=', stock_location.id),
                ('location_id', '=', ksx_location.id),
            ], 0, 0, 'date asc')
            stock_move_ins.create_production_transfer_quant()

            # STEP6: Disassemble Increase
            disassemble_move_ids  = []
            disassemble_materials = self.env['disassemble.materials'].search([
                ('product_id', '=', product.id),
                ('move_id', '!=', False),
                ('move_id.state', '=', 'done'),
            ])
            for material in disassemble_materials:
                if material.move_id and material.move_id.state == 'done':
                    if material.move_id.id not in disassemble_move_ids:
                        material.move_id.create_disassemble_output_quant()
                        disassemble_move_ids.append(material.move_id.id)

            # STEP7: Material return quant
            stock_move_ins = self.env['stock.move'].search([
                ('product_id', '=', product.id),
                ('state', '=', 'done'),
                ('location_dest_id', '=', stock_location.id),
                ('location_id', '=', production_location.id),
                ('id', 'not in', disassemble_move_ids),
            ], 0, 0, 'date asc')
            for stock_move in stock_move_ins:
                stock_move.create_material_return_quant()

            last_location_id = False
            location_ids     = [stock_location.id, ksx_location.id]

            for location_id in location_ids:
                stock_move_outs = self.env['stock.move'].search([
                    ('product_id', '=', product.id),
                    ('state', '=', 'done'),
                    ('location_id', '=', location_id),
                    ('location_dest_id', '!=', location_id),
                    ('location_dest_id', '!=', last_location_id),
                ], 0, 0, 'date asc')
                did_reset_pickings = []
                for stock_move in stock_move_outs:
                    if stock_move.picking_id and stock_move.picking_id.pack_operation_product_ids:
                        if stock_move.picking_id.id not in did_reset_pickings:
                            move_outs = self.env['stock.move'].search([
                                ('picking_id', '=', stock_move.picking_id.id),
                                ('product_id', '=', product.id),
                                ('state', '=', 'done'),
                                ('location_id', '=', location_id),
                                ('location_dest_id', '!=', location_id),
                            ], 0, 0, 'date asc')

                            query = "UPDATE stock_move SET state='confirmed' WHERE id IN (%s)" % (','.join(str(v) for v in move_outs.ids),)
                            self.env.cr.execute(query)

                            move_outs.action_assign()
                            move_outs.with_context(force_period_date=stock_move.date).action_done()

                            did_reset_pickings.append(stock_move.picking_id.id)

                    else:
                        query = "UPDATE stock_move SET state='confirmed' WHERE id = %s" % (stock_move.id,)
                        self.env.cr.execute(query)

                        stock_move.action_assign()
                        stock_move.with_context(force_period_date=stock_move.date).action_done()

                last_location_id = location_id

            product.update_disassemble_price()
            product.update_marerial_return_price()
            product.update_mrp_price()
            product.update_sale_return_price()

            stock_move_done_after = self.env['stock.move'].search([
                ('product_id', '=', product.id),
                ('state', '=', 'done'),
            ], count=True)

            if stock_move_done_before != stock_move_done_after:
                _logger.info('AAAA:Stock Move done error %s, Before: %s - After: %s' %(product.id, stock_move_done_before, stock_move_done_after))
                continue

            account_move_done_after = self.env['account.move.line'].search([
                ('product_id', '=', product.id),
            ], count=True)

            if account_move_done_before != account_move_done_after:
                self.env.cr.commit()
                message = 'SSSS:Account Move done error %s, Before: %s - After: %s' %(product.id, account_move_done_before, account_move_done_after)
                _logger.info(message)
                continue

        # return True

    @api.model
    def create(self, values):
        record = super(ProductProduct, self).create(values)
        return record

    @api.multi
    def write(self, values):
        result = super(ProductProduct, self).write(values)
        return result