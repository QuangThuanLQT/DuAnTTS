# -*- coding: utf-8 -*-
import os
import xmlrpclib
import xlrd
import datetime
from odoo import models, fields, api

dir_path = os.path.dirname(os.path.realpath(__file__))

class tuanhuy_base(models.Model):
    _name = 'tuanhuy.base'

    @api.model
    def execute_query(self, query, get_result=False):
        self.env.cr.execute(query)
        if get_result:
            results = self.env.cr.fetchall()
            return results
        return True

    @api.model
    def cron_picking_off(self):
        query = "UPDATE ir_cron SET active=false WHERE name = '%s'" % ('Cron Create Picking From Sale',)
        self.execute_query(query)
        return True

    @api.model
    def cron_picking_on(self):
        query = "UPDATE ir_cron SET active=true WHERE name = '%s'" % ('Cron Create Picking From Sale',)
        self.execute_query(query)
        return True

    @api.model
    def get_po_picking_dones(self):
        po_picking_dones = []
        query = "SELECT origin FROM stock_picking WHERE state='%s' AND origin LIKE '%s' ORDER BY min_date asc" % ('done', 'PO%')
        query_result = self.execute_query(query, True)
        if query_result and len(query_result) > 0:
            for query_line in query_result:
                po_picking_dones.append(query_line[0])
        return po_picking_dones

    @api.model
    def get_po_picking_assigned(self):
        po_picking_assigned = []
        query = "SELECT origin FROM stock_picking WHERE state IN ('assigned', 'partially_available') AND origin LIKE '%s' ORDER BY min_date asc" % ('PO%')
        query_result = self.execute_query(query, True)
        if query_result and len(query_result) > 0:
            for query_line in query_result:
                po_picking_assigned.append(query_line[0])
        return po_picking_assigned

    @api.model
    def get_return_has_so(self):
        return_has_so = []
        query = "SELECT DISTINCT so.name, so.date_order FROM sale_order_return_rel sr INNER JOIN sale_order so ON so.id = sr.order_id WHERE so.state = 'sale' AND so.sale_order_return = true ORDER BY so.date_order asc"
        query_result = self.execute_query(query, True)
        if query_result and len(query_result) > 0:
            for query_line in query_result:
                return_has_so.append(query_line[0])
        return return_has_so

    @api.model
    def get_return_no_so(self):
        return_has_so = self.get_return_has_so()

        return_no_so = []
        query = "SELECT DISTINCT so.name, so.date_order FROM sale_order so WHERE so.state = 'sale' AND so.sale_order_return = true AND so.name NOT IN ('%s') ORDER BY so.date_order asc" % ("','".join(return_has_so))
        query_result = self.execute_query(query, True)
        if query_result and len(query_result) > 0:
            for query_line in query_result:
                return_no_so.append(query_line[0])
        return return_no_so

    @api.model
    def get_return_no_so_done(self):
        return_no_so = self.get_return_no_so()

        return_no_so_done = []
        query = "SELECT origin FROM stock_picking WHERE state = 'done' AND origin IN ('%s') ORDER BY min_date asc" % ("','".join(return_no_so),)
        query_result = self.execute_query(query, True)
        if query_result and len(query_result) > 0:
            for query_line in query_result:
                return_no_so_done.append(query_line[0])

        return return_no_so_done

    @api.model
    def get_so_has_return(self):
        so_has_return = []
        query = "SELECT DISTINCT so.name, so.date_order FROM sale_order_return_rel sr INNER JOIN sale_order so ON so.id = sr.sale_order_return_relation WHERE so.state = 'sale' AND so.sale_order_return = false ORDER BY so.date_order asc"
        query_result = self.execute_query(query, True)
        if query_result and len(query_result) > 0:
            for query_line in query_result:
                so_has_return.append(query_line[0])
        return so_has_return

    @api.model
    def get_so_has_return_done(self):
        so_has_return = self.get_so_has_return()

        so_has_return_done = []
        query = "SELECT origin FROM stock_picking WHERE state = 'done' AND origin IN ('%s') ORDER BY min_date asc" % ("','".join(so_has_return),)
        query_result = self.execute_query(query, True)
        if query_result and len(query_result) > 0:
            for query_line in query_result:
                so_has_return_done.append(query_line[0])
        return so_has_return_done

    @api.model
    def get_return_has_so_done(self):
        return_has_so = self.get_return_has_so()

        return_has_so_done = []
        query = "SELECT origin FROM stock_picking WHERE state = 'done' AND origin IN ('%s') ORDER BY min_date asc" % ("','".join(return_has_so),)
        query_result = self.execute_query(query, True)
        if query_result and len(query_result) > 0:
            for query_line in query_result:
                return_has_so_done.append(query_line[0])

        return return_has_so_done

    @api.model
    def get_rtp_picking_dones(self):
        rtp_picking_dones = []
        query = "SELECT origin FROM stock_picking WHERE state = 'done' AND origin LIKE '%s' ORDER BY min_date asc" % ('RTP%')
        query_result = self.execute_query(query, True)
        if query_result and len(query_result) > 0:
            for query_line in query_result:
                rtp_picking_dones.append(query_line[0])
        return rtp_picking_dones

    @api.model
    def get_rtp_picking_assigned(self):
        rtp_picking_assigned = []
        query = "SELECT origin FROM stock_picking WHERE state IN ('assigned', 'partially_available') AND origin LIKE '%s' ORDER BY min_date asc" % ('RTP%')
        query_result = self.execute_query(query, True)
        if query_result and len(query_result) > 0:
            for query_line in query_result:
                rtp_picking_assigned.append(query_line[0])
        return rtp_picking_assigned

    @api.model
    def get_so_picking_dones(self):
        so_picking_dones = []
        query = "SELECT origin FROM stock_picking WHERE state = 'done' AND origin LIKE '%s' ORDER BY min_date asc" % ('SO%')
        query_result = self.execute_query(query, True)
        if query_result and len(query_result) > 0:
            for query_line in query_result:
                so_picking_dones.append(query_line[0])
        return so_picking_dones

    @api.model
    def get_so_picking_assigned(self):
        so_picking_assigned = []
        query = "SELECT origin FROM stock_picking WHERE state IN ('assigned', 'partially_available') AND origin LIKE '%s' ORDER BY min_date asc" % ('SO%')
        query_result = self.execute_query(query, True)
        if query_result and len(query_result) > 0:
            for query_line in query_result:
                so_picking_assigned.append(query_line[0])
        return so_picking_assigned

    @api.model
    def get_so_picking_confirmed(self):
        so_picking_confirmed = []
        query = "SELECT origin FROM stock_picking WHERE state = 'confirmed' AND origin LIKE '%s' ORDER BY min_date asc" % ('SO%')
        query_result = self.execute_query(query, True)
        if query_result and len(query_result) > 0:
            for query_line in query_result:
                so_picking_confirmed.append(query_line[0])
        return so_picking_confirmed

    @api.model
    def step1_update_cost_price(self):
        cost_file_path = '%s/%s' % (dir_path, 'tuanhuy-cost.xls')

        workbook = xlrd.open_workbook(cost_file_path)
        worksheet = workbook.sheet_by_index(0)

        num_rows = worksheet.nrows - 1
        # num_cells = worksheet.ncols - 1
        curr_row = 0

        while curr_row < num_rows:
            curr_row += 1
            row = worksheet.row(curr_row)

            if len(row) > 9:
                default_code = row[0].value
                product_cost = float(row[9].value)

                if default_code and product_cost:
                    products = self.env['product.template'].search([
                        ('default_code', '=', default_code),
                    ])
                    if len(products) == 1:
                        products.write({
                            'standard_price': product_cost,
                        })
                else:
                    pass
        return True

    @api.model
    def step2_remove_account_move(self):
        stock_journal_id = 7
        query = "DELETE FROM account_move_line WHERE move_id IN (SELECT id FROM account_move WHERE journal_id = %s)" % (stock_journal_id,)
        self.execute_query(query)

        query = "DELETE FROM account_move WHERE journal_id = %s" % (stock_journal_id,)
        self.execute_query(query)

        return True

    @api.model
    def step3_remove_stock_quant(self):
        query = "DELETE FROM stock_quant"
        self.execute_query(query)

        return True

    @api.model
    def step4_remove_stock_pack_operation(self):
        query = "DELETE FROM stock_pack_operation"
        self.execute_query(query)

        return True

    @api.model
    def step5_remove_stock_move(self):
        query = "DELETE FROM stock_move WHERE inventory_id IS NOT NULL"
        self.execute_query(query)

        return True

    @api.model
    def step6_reset_stock_inventory(self):
        query = "UPDATE stock_inventory SET state='confirm'"
        self.execute_query(query)

        return True

    @api.model
    def step7_confirm_stock_inventory(self):
        inventories = self.env['stock.inventory'].search([
            ('state', '=', 'confirm'),
        ], 0, 0, 'date asc')
        for inventory in inventories:
            inventory.action_done()

        return True

    @api.model
    def reset_and_confirm_picking(self, origins):
        if origins and len(origins) > 0:
            pickings = self.env['stock.picking'].search([
                ('origin', 'in', origins),
            ], 0, 0, 'min_date asc')
            for picking in pickings:
                query = "UPDATE stock_move SET state='draft' WHERE picking_id = %s" % (picking.id,)
                self.execute_query(query)

                query = "UPDATE stock_picking SET state='draft' WHERE id = %s" % (picking.id,)
                self.execute_query(query)

                # confirm & validate the picking
                picking.action_confirm()
                picking.do_new_transfer()

    @api.model
    def reset_picking(self, origins):
        if origins and len(origins) > 0:
            pickings = self.env['stock.picking'].search([
                ('origin', 'in', origins),
            ], 0, 0, 'min_date asc')
            for picking in pickings:
                query = "UPDATE stock_move SET state='draft' WHERE picking_id = %s" % (picking.id,)
                self.execute_query(query)

                query = "UPDATE stock_picking SET state='draft' WHERE id = %s" % (picking.id,)
                self.execute_query(query)

                # confirm & validate the picking
                picking.action_confirm()

    @api.model
    def step8_reset_purchase(self):
        po_picking_dones = self.get_po_picking_dones()
        self.reset_and_confirm_picking(po_picking_dones)

    @api.model
    def step9_reset_purchase_assigned(self):
        po_picking_assigned = self.get_po_picking_assigned()
        self.reset_picking(po_picking_assigned)

    @api.model
    def step10_reset_return_no_so_done(self):
        return_no_so_done = self.get_return_no_so_done()
        self.reset_and_confirm_picking(return_no_so_done)

    @api.model
    def step11_reset_so_has_return_done(self):
        so_has_return_done = self.get_so_has_return_done()
        self.reset_and_confirm_picking(so_has_return_done)

    @api.model
    def step12_reset_return_has_so_done(self):
        return_has_so_done = self.get_return_has_so_done()
        self.reset_and_confirm_picking(return_has_so_done)

    @api.model
    def step13_reset_rtp_picking_dones(self):
        rtp_picking_dones = self.get_rtp_picking_dones()
        self.reset_and_confirm_picking(rtp_picking_dones)

    @api.model
    def step14_reset_rtp_picking_assigned(self):
        rtp_picking_assigned = self.get_rtp_picking_assigned()
        self.reset_picking(rtp_picking_assigned)

    @api.model
    def step15_reset_so_picking_dones(self):
        so_picking_dones = self.get_so_picking_dones()
        self.reset_and_confirm_picking(so_picking_dones)

    @api.model
    def step16_reset_so_picking_assigned(self):
        so_picking_assigned = self.get_so_picking_assigned()
        self.reset_picking(so_picking_assigned)

    @api.model
    def step17_update_move_date(self):
        query = "UPDATE account_move SET date = stock_picking.min_date FROM stock_picking WHERE stock_picking.name = account_move.ref AND account_move.ref IS NOT NULL AND account_move.ref LIKE 'WH/OUT/%'"
        self.execute_query(query)

        query = "UPDATE account_move_line SET date = account_move.date FROM account_move WHERE account_move.id = account_move_line.move_id AND account_move.ref IS NOT NULL AND account_move.ref LIKE 'WH/OUT/%'"
        self.execute_query(query)

        query = "UPDATE account_move SET date = stock_picking.min_date FROM stock_picking WHERE stock_picking.name = account_move.ref AND account_move.ref IS NOT NULL AND account_move.ref LIKE 'WH/IN/%'"
        self.execute_query(query)

        query = "UPDATE account_move_line SET date = account_move.date FROM account_move WHERE account_move.id = account_move_line.move_id AND account_move.ref IS NOT NULL AND account_move.ref LIKE 'WH/IN/%'"
        self.execute_query(query)

    @api.model
    def main_action(self):
        self.cron_picking_off()

        self.step1_update_cost_price()
        self.step2_remove_account_move()
        self.step3_remove_stock_quant()
        self.step4_remove_stock_pack_operation()
        self.step5_remove_stock_move()
        self.step6_reset_stock_inventory()
        self.step7_confirm_stock_inventory()
        self.step8_reset_purchase()
        self.step9_reset_purchase_assigned()
        self.step10_reset_return_no_so_done()
        self.step11_reset_so_has_return_done()
        self.step12_reset_return_has_so_done()
        self.step13_reset_rtp_picking_dones()
        self.step14_reset_rtp_picking_assigned()
        self.step15_reset_so_picking_dones()
        self.step16_reset_so_picking_assigned()
        self.step17_update_move_date()

        self.cron_picking_on()