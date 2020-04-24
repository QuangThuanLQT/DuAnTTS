# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    price_unit_sub  = fields.Float(compute='get_price_unit_sub', digits=(16,0))
    price_unit_sale = fields.Float(compute='get_price_unit_sale', digits=(16,0))
    sale_select_id  = fields.Many2one('sale.order', 'Đơn hàng', related='picking_id.sale_select_id')
    picking_origin  = fields.Char('Nguồn',related='picking_id.origin')
    stt             = fields.Integer('STT')
    weight_uom_id   = fields.Many2one('product.uom',required=False)
    sale_stock_out_id = fields.Many2one('sale.order',string='Đơn hàng')

    @api.multi
    def get_price_unit_sale(self):
        for rec in self:
            sale_id = rec.picking_id.sale_id or rec.sale_select_id
            sale_line_id = sale_id.order_line.filtered(lambda l: l.product_id == rec.product_id)
            if sale_line_id:
                sale_line_id = sale_line_id[0]
                rec.price_unit_sale = sale_line_id.last_price_unit

    @api.multi
    def get_price_unit_sub(self):
        for rec in self:
            rec.price_unit_sub = rec.price_unit
            if not rec.price_unit_sub:
                if sum(rec.quant_ids.mapped('qty')):
                    rec.price_unit_sub = sum(rec.quant_ids.mapped('inventory_value')) / sum(rec.quant_ids.mapped('qty'))

    @api.depends('product_uom_qty', 'location_id', 'location_dest_id')
    def _get_quantity(self):
        stock_location = self.env.ref('stock.stock_location_stock')
        for record in self:
            if record.location_id.id == stock_location.id:
                if record.location_dest_id.id == stock_location.id:
                    record.quantity_in  = record.product_uom_qty
                    record.quantity_out = record.product_uom_qty
                else:
                    record.quantity_in  = 0
                    record.quantity_out = record.product_uom_qty
            else:
                if record.location_dest_id.id == stock_location.id:
                    record.quantity_in  = record.product_uom_qty
                    record.quantity_out = 0
                else:
                    record.quantity_in  = record.product_uom_qty
                    record.quantity_out = record.product_uom_qty
            # if record.location_dest_id.name == 'Stock' and record.location_id.name == 'Stock':
            #     if record.picking_id and record.picking_id.picking_type_code == 'internal':
            #         if record.location_id.location_id and record.location_id.location_id.name == 'WH':
            #             record.quantity_in = 0
            #             record.quantity_out = record.product_uom_qty
            #         elif record.location_dest_id.location_id and record.location_dest_id.location_id.name == 'WH':
            #             record.quantity_in = record.product_uom_qty
            #             record.quantity_out = 0
            #     else:
            #         record.quantity_in = record.product_uom_qty
            #         record.quantity_out = record.product_uom_qty
            # elif record.location_dest_id.name == 'Stock':
            #     record.quantity_in = record.product_uom_qty
            #     record.quantity_out = 0
            # else:
            #     record.quantity_in = 0
            #     record.quantity_out = record.product_uom_qty

    @api.multi
    def update_stock_move_quantity_in_out(self):
        for record in self.search([]):
            record._get_quantity()

    def _get_remain_qty_dk(self):
        for record in self:
            parent_id = self.env['stock.location'].search([('name', '=', 'WH')], limit=1)
            query_in_1 = """SELECT SUM(m.product_uom_qty) AS total_qty 
                            FROM stock_move m INNER JOIN stock_location l ON l.id = m.location_dest_id 
                            WHERE m.product_id = '%s' AND l.name = 'Stock' AND l.location_id = '%s' AND m.date < '%s' AND m.state = 'done'"""% \
                         (record.product_id.id, parent_id.id, record.date)
            self.env.cr.execute(query_in_1)
            sum_in_1 = self.env.cr.fetchall()
            if sum_in_1 and len(sum_in_1) > 0:
                sum_in_1 = sum_in_1[0][0] or 0
            else:
                sum_in_1 = 0

            query_in_2 = """SELECT SUM(m.product_uom_qty) AS total_qty 
                            FROM stock_move m INNER JOIN stock_location l ON l.id = m.location_dest_id 
                            WHERE m.product_id = '%s' AND l.name = 'Stock' AND l.location_id = '%s' AND m.date = '%s' AND m.id < '%s' AND m.state = 'done'""" % \
                         (record.product_id.id, parent_id.id, record.date,record.id)
            self.env.cr.execute(query_in_2)
            sum_in_2 = self.env.cr.fetchall()
            if sum_in_2 and len(sum_in_2) > 0:
                sum_in_2 = sum_in_2[0][0] or 0
            else:
                sum_in_2 = 0

            query_out_1 = """SELECT SUM(m.product_uom_qty) AS total_qty 
                              FROM stock_move m INNER JOIN stock_location l ON l.id = m.location_id 
                              WHERE m.product_id = '%s' AND l.name = 'Stock' AND l.location_id = '%s' AND m.date < '%s' AND m.state = 'done'"""% \
                          (record.product_id.id, parent_id.id, record.date)
            self.env.cr.execute(query_out_1)
            sum_out_1 = self.env.cr.fetchall()
            if sum_out_1 and len(sum_out_1) > 0:
                sum_out_1 = sum_out_1[0][0] or 0
            else:
                sum_out_1 = 0

            query_out_2 = """SELECT SUM(m.product_uom_qty) AS total_qty 
                              FROM stock_move m INNER JOIN stock_location l ON l.id = m.location_id 
                              WHERE m.product_id = '%s' AND l.name = 'Stock' AND l.location_id = '%s' AND m.date = '%s' AND m.id < '%s' AND m.state = 'done'""" % \
                         (record.product_id.id, parent_id.id, record.date, record.id)
            self.env.cr.execute(query_out_2)
            sum_out_2 = self.env.cr.fetchall()
            if sum_out_2 and len(sum_out_2) > 0:
                sum_out_2 = sum_out_2[0][0] or 0
            else:
                sum_out_2 = 0

            remain_qty_dk = sum_in_1 + sum_in_2 - sum_out_1 - sum_out_2
            record.remain_qty_dk = remain_qty_dk

    def _get_remain_qty_dk_not_cancel(self):
        for record in self:
            parent_id = self.env['stock.location'].search([('name', '=', 'WH')], limit=1)
            query_in_1 = """SELECT SUM(m.product_uom_qty) AS total_qty 
                            FROM stock_move m INNER JOIN stock_location l ON l.id = m.location_dest_id 
                            WHERE m.product_id = '%s' AND l.name = 'Stock' AND l.location_id = '%s' AND m.date < '%s' AND m.state not in ('draft','cancel')"""% \
                         (record.product_id.id, parent_id.id, record.date)
            self.env.cr.execute(query_in_1)
            sum_in_1 = self.env.cr.fetchall()
            if sum_in_1 and len(sum_in_1) > 0:
                sum_in_1 = sum_in_1[0][0] or 0
            else:
                sum_in_1 = 0

            query_in_2 = """SELECT SUM(m.product_uom_qty) AS total_qty 
                            FROM stock_move m INNER JOIN stock_location l ON l.id = m.location_dest_id 
                            WHERE m.product_id = '%s' AND l.name = 'Stock' AND l.location_id = '%s' AND m.date = '%s' AND m.id < '%s' AND m.state not in ('draft','cancel')""" % \
                         (record.product_id.id, parent_id.id, record.date, record.id)
            self.env.cr.execute(query_in_2)
            sum_in_2 = self.env.cr.fetchall()
            if sum_in_2 and len(sum_in_2) > 0:
                sum_in_2 = sum_in_2[0][0] or 0
            else:
                sum_in_2 = 0

            query_out_1 = """SELECT SUM(m.product_uom_qty) AS total_qty 
                              FROM stock_move m INNER JOIN stock_location l ON l.id = m.location_id 
                              WHERE m.product_id = '%s' AND l.name = 'Stock' AND l.location_id = '%s' AND m.date < '%s' AND m.state not in ('draft','cancel')"""% \
                          (record.product_id.id, parent_id.id, record.date)
            self.env.cr.execute(query_out_1)
            sum_out_1 = self.env.cr.fetchall()
            if sum_out_1 and len(sum_out_1) > 0:
                sum_out_1 = sum_out_1[0][0] or 0
            else:
                sum_out_1 = 0

            query_out_2 = """SELECT SUM(m.product_uom_qty) AS total_qty 
                              FROM stock_move m INNER JOIN stock_location l ON l.id = m.location_id 
                              WHERE m.product_id = '%s' AND l.name = 'Stock'AND l.location_id = '%s'  AND m.date = '%s' AND m.id < '%s' AND m.state not in ('draft','cancel')""" % \
                         (record.product_id.id, parent_id.id, record.date, record.id)
            self.env.cr.execute(query_out_2)
            sum_out_2 = self.env.cr.fetchall()
            if sum_out_2 and len(sum_out_2) > 0:
                sum_out_2 = sum_out_2[0][0] or 0
            else:
                sum_out_2 = 0

            remain_qty_dk = sum_in_1 + sum_in_2 - sum_out_1 - sum_out_2
            return remain_qty_dk

    @api.multi
    def action_done(self):
        res = super(StockMove, self).action_done()
        for stock in self:
            if stock.picking_id and stock.picking_id.min_date:
                stock.write({'date': stock.picking_id.min_date})
                for quant in stock.quant_ids:
                    quant.in_date = stock.picking_id.min_date
        return res

    @api.multi
    def action_assign(self, no_prepare=False):
        Quant = self.env['stock.quant']

        res = super(StockMove, self).action_assign(no_prepare=no_prepare)
        for move in self:
            if move.state == 'waiting' and move.move_orig_ids:
                quant_domain = [
                    ('reservation_id', '=', False),
                    ('qty', '>', 0),
                    ('history_ids', 'in', move.move_orig_ids.ids)
                ]
                qty_already_assigned = move.reserved_availability
                qty = move.product_qty - qty_already_assigned

                quants = Quant.quants_get_preferred_domain(qty, move, domain=quant_domain, preferred_domain_list=[])
                Quant.quants_reserve(quants, move)
        return res

    @api.multi
    def write(self, values):
        res = super(StockMove, self).write(values)
        return res

    @api.multi
    def action_confirm(self):
        res = super(StockMove, self).action_confirm()
        for move in self:
            if move.state == 'waiting' and move.move_orig_ids:
                super(StockMove, move).recalculate_move_state()
        return res

    @api.multi
    def multi_do_unreserve(self):
        move_ids = []
        if self.env.context.get('active_ids',False) and self.env.context.get('active_model',False) == 'stock.move':
            move_ids = self.env['stock.move'].browse(self.env.context.get('active_ids',False))
            move_ids.do_unreserve()

    @api.multi
    def multi_action_assign(self):
        move_ids = []
        if self.env.context.get('active_ids', False) and self.env.context.get('active_model', False) == 'stock.move':
            move_ids = self.env['stock.move'].browse(self.env.context.get('active_ids', False))
        if move_ids:
            stock_moves = move_ids.filtered(lambda rec:rec.state in ['confirmed', 'partially_available','assigned'])
            for move in stock_moves:
                move.do_unreserve()
                move.action_assign()
                if move.state == 'confirmed':
                    move.action_assign()

    @api.multi
    def multi_do_new_transfer(self):
        move_ids = []
        if self.env.context.get('active_ids', False) and self.env.context.get('active_model', False) == 'stock.move':
            move_ids = self.env['stock.move'].browse(self.env.context.get('active_ids', False))
        for move in move_ids:
            if move.state in ['assigned']:
                move.action_done()

class stock_quant(models.Model):
    _inherit = 'stock.quant'

    def _create_account_move_line(self, move, credit_account_id, debit_account_id, journal_id):
        if move.picking_id and move.picking_id.picking_type_id == self.env.ref('cptuanhuy_stock.manufacturing_transfer'):
            if len(move.picking_id.picking_type_id.account_analytic_ids.ids):
                self = self.with_context(force_set_analytic_tag_by_picking_type=move.picking_id.picking_type_id.account_analytic_ids.ids)
        res = super(stock_quant, self)._create_account_move_line(move, credit_account_id, debit_account_id, journal_id)
        return res