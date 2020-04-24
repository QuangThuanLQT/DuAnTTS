# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json
from collections import defaultdict
from odoo.addons import decimal_precision as dp


class stock_move_ihr(models.Model):
    _inherit = 'stock.move'

    check_is_pick = fields.Boolean(related='picking_id.check_is_pick')
    color = fields.Char()
    size = fields.Char()
    area = fields.Char()
    line = fields.Char()
    product_location_ids = fields.Char(compute='_get_location_domain')
    check_is_pick = fields.Boolean(compute='_get_check_is_pick')
    check_is_pack = fields.Boolean(compute='_get_check_is_pick')
    check_is_delivery = fields.Boolean(compute='_get_check_is_pick')
    is_internal_transfer = fields.Boolean(compute='check_is_internal_transfer')
    product_qty_missing = fields.Float(digits=dp.get_precision('Product Unit of Measure'))
    remain_qty = fields.Float(digits=dp.get_precision('Product Unit of Measure'))
    remain_qty_dk = fields.Float(digits=dp.get_precision('Product Unit of Measure'))
    quantity_in = fields.Float(digits=dp.get_precision('Product Unit of Measure'), compute='get_quantity_in_out')
    quantity_out = fields.Float(digits=dp.get_precision('Product Unit of Measure'), compute='get_quantity_in_out')
    quantity_du_bao = fields.Float(digits=dp.get_precision('Product Unit of Measure'))
    move_in_out = fields.Char(compute='get_move_in_out', store=True)
    product_cost = fields.Float('Giá vốn', compute='update_product_cost', store=True)

    @api.depends('state', 'date')
    def update_product_cost(self):
        for record in self:
            if record.state == 'done':
                if record.id == 331348:
                    True
                if record.location_id.usage == 'procurement' and record.location_dest_id.usage == 'internal':
                    if record.picking_id.sale_id and record.picking_id.sale_id.sale_order_return == True:
                        if record.picking_id.sale_id.sale_order_return_ids:
                            order_return = record.picking_id.sale_id.sale_order_return_ids[0]
                            if order_return.invoice_ids:
                                invoice_id = order_return.invoice_ids[0]
                                date_order = invoice_id.create_date
                            else:
                                date_order = order_return.confirmation_date
                        else:
                            date_order = record.picking_id.sale_id.confirmation_date
                        amount_cost_sale = record.product_id.get_history_price(record.company_id.id, date_order)
                        record.product_cost = amount_cost_sale
                    else:
                        amount_cost_sale = record.product_id.get_history_price(record.company_id.id, record.date)
                        record.product_cost = amount_cost_sale
                else:
                    amount_cost_sale = record.product_id.get_history_price(record.company_id.id, record.date)
                    record.product_cost = amount_cost_sale

    @api.depends('location_id', 'location_dest_id')
    def get_move_in_out(self):
        for record in self:
            check_stock_move_in_out = record.check_stock_move_in_out()
            record.move_in_out = check_stock_move_in_out

    def check_stock_move_in_out(self):
        stock_location_stock = self.env.ref('stock.stock_location_stock')
        stock_location_suppliers = self.env.ref('stock.stock_location_suppliers')
        stock_location_customers = self.env.ref('stock.stock_location_customers')
        stock_location_scrapped = self.env.ref('stock.stock_location_scrapped')
        location_inventory = self.env.ref('stock.location_inventory')
        location_procurement = self.env.ref('stock.location_procurement')

        not_sellable = self.env['stock.location'].search([('not_sellable', '=', True)])

        if (self.location_id == location_procurement and self.location_dest_id == stock_location_stock) or \
                (self.location_id == location_procurement and self.location_dest_id in not_sellable) or \
                (self.location_id == location_inventory and self.location_dest_id == stock_location_stock) or \
                (self.location_id == location_inventory and self.location_dest_id in not_sellable):
            return 'in'
        elif self.location_dest_id in [stock_location_scrapped, location_inventory, stock_location_customers]:
            return 'out'
        else:
            return 'dont_know'

    @api.depends('product_uom_qty', 'location_id', 'location_dest_id')
    def get_quantity_in_out(self):
        for record in self:
            check_stock_move_in_out = record.check_stock_move_in_out()
            if check_stock_move_in_out == 'in':
                record.quantity_in = record.product_uom_qty
                record.quantity_out = 0
            elif check_stock_move_in_out == 'out':
                record.quantity_in = 0
                record.quantity_out = record.product_uom_qty
            else:
                record.quantity_in = 0
                record.quantity_out = 0

    def _get_remain_qty_dk(self):
        for record in self:
            query_in_1 = """SELECT SUM(m.product_uom_qty) AS total_qty FROM stock_move m 
            WHERE m.product_id = '%s' AND m.move_in_out = 'in' AND m.date < '%s' AND m.state = 'done'""" % (
            record.product_id.id, record.date)
            self.env.cr.execute(query_in_1)
            sum_in_1 = self.env.cr.fetchall()
            if sum_in_1 and len(sum_in_1) > 0:
                sum_in_1 = sum_in_1[0][0] or 0
            else:
                sum_in_1 = 0

            query_in_2 = """SELECT SUM(m.product_uom_qty) AS total_qty FROM stock_move m 
            WHERE m.product_id = '%s' AND m.move_in_out = 'in' AND m.date = '%s' AND m.id < '%s' AND m.state = 'done'""" % \
                         (record.product_id.id, record.date, record.id)
            self.env.cr.execute(query_in_2)
            sum_in_2 = self.env.cr.fetchall()
            if sum_in_2 and len(sum_in_2) > 0:
                sum_in_2 = sum_in_2[0][0] or 0
            else:
                sum_in_2 = 0

            query_out_1 = """SELECT SUM(m.product_uom_qty) AS total_qty FROM stock_move m 
            WHERE m.product_id = '%s' AND m.move_in_out = 'out' AND m.date < '%s' AND m.state = 'done'""" % (
            record.product_id.id, record.date)
            self.env.cr.execute(query_out_1)
            sum_out_1 = self.env.cr.fetchall()
            if sum_out_1 and len(sum_out_1) > 0:
                sum_out_1 = sum_out_1[0][0] or 0
            else:
                sum_out_1 = 0

            query_out_2 = """SELECT SUM(m.product_uom_qty) AS total_qty FROM stock_move m 
                                    WHERE m.product_id = '%s' AND m.move_in_out = 'out' AND m.date = '%s' AND m.id < '%s' AND m.state = 'done'""" % \
                          (record.product_id.id, record.date, record.id)
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
            query_in_1 = """SELECT SUM(m.product_uom_qty) AS total_qty FROM stock_move m 
            WHERE m.product_id = '%s' AND m.move_in_out = 'in' AND m.date < '%s' AND m.state not in ('draft','cancel')""" % (
            record.product_id.id, record.date)
            self.env.cr.execute(query_in_1)
            sum_in_1 = self.env.cr.fetchall()
            if sum_in_1 and len(sum_in_1) > 0:
                sum_in_1 = sum_in_1[0][0] or 0
            else:
                sum_in_1 = 0

            query_in_2 = """SELECT SUM(m.product_uom_qty) AS total_qty FROM stock_move m 
                        WHERE m.product_id = '%s' AND m.move_in_out = 'in' AND m.date = '%s' AND m.id < '%s' AND m.state not in ('draft','cancel')""" % \
                         (record.product_id.id, record.date, record.id)
            self.env.cr.execute(query_in_2)
            sum_in_2 = self.env.cr.fetchall()
            if sum_in_2 and len(sum_in_2) > 0:
                sum_in_2 = sum_in_2[0][0] or 0
            else:
                sum_in_2 = 0

            query_out_1 = """SELECT SUM(m.product_uom_qty) AS total_qty FROM stock_move m 
            WHERE m.product_id = '%s' AND m.move_in_out = 'out' AND m.date < '%s' AND m.state not in ('draft','cancel')""" % (
            record.product_id.id, record.date)
            self.env.cr.execute(query_out_1)
            sum_out_1 = self.env.cr.fetchall()
            if sum_out_1 and len(sum_out_1) > 0:
                sum_out_1 = sum_out_1[0][0] or 0
            else:
                sum_out_1 = 0

            query_out_2 = """SELECT SUM(m.product_uom_qty) AS total_qty FROM stock_move m 
                                    WHERE m.product_id = '%s' AND m.move_in_out = 'in' AND m.date = '%s' AND m.id < '%s' AND m.state not in ('draft','cancel')""" % \
                          (record.product_id.id, record.date, record.id)
            self.env.cr.execute(query_out_2)
            sum_out_2 = self.env.cr.fetchall()
            if sum_out_2 and len(sum_out_2) > 0:
                sum_out_2 = sum_out_2[0][0] or 0
            else:
                sum_out_2 = 0

            remain_qty_dk = sum_in_1 + sum_in_2 - sum_out_1 - sum_out_2
            return remain_qty_dk

    @api.multi
    def product_price_update_before_done(self):
        tmpl_dict = defaultdict(lambda: 0.0)
        # adapt standard price on incomming moves if the product cost_method is 'average'
        std_price_update = {}
        for move in self.filtered(lambda move: move.location_id.usage in ('procurement')
        and move.product_id.cost_method == 'average' and not move.location_dest_id.not_sellable and move.location_dest_id.usage == 'internal'):
            product_tot_qty_available = move.product_id.qty_available + tmpl_dict[move.product_id.id]
            if move.picking_id.picking_from_sale_return:
                if move.picking_id.sale_id.sale_order_return_ids:
                    order_return = move.picking_id.sale_id.sale_order_return_ids[0]
                    if order_return.invoice_ids:
                        invoice_id = order_return.invoice_ids[0]
                        date_order = invoice_id.create_date
                    else:
                        date_order = order_return.confirmation_date
                else:
                    date_order = move.picking_id.sale_id.confirmation_date
                amount_unit = std_price_update.get(
                    (move.company_id.id, move.product_id.id)) or move.product_id.standard_price
                amount_cost_sale = move.product_id.get_history_price(move.company_id.id, date_order)
                new_std_price = ((amount_unit * product_tot_qty_available) + (
                    amount_cost_sale * move.product_qty)) / (product_tot_qty_available + move.product_qty)
            else:
                # if the incoming move is for a purchase order with foreign currency, need to call this to get the same value that the quant will use.
                if product_tot_qty_available <= 0:
                    new_std_price = move.get_price_unit()
                else:
                    # Get the standard price
                    amount_unit = std_price_update.get(
                        (move.company_id.id, move.product_id.id)) or move.product_id.standard_price
                    new_std_price = ((amount_unit * product_tot_qty_available) + (
                        move.get_price_unit() * move.product_qty)) / (product_tot_qty_available + move.product_qty)

            tmpl_dict[move.product_id.id] += move.product_qty
            # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
            move.product_id.with_context(force_company=move.company_id.id).sudo().write(
                {'standard_price': new_std_price})
            std_price_update[move.company_id.id, move.product_id.id] = new_std_price

    @api.onchange('picking_type_id')
    def check_is_internal_transfer(self):
        for rec in self:
            origin = rec.origin or ''
            if rec.picking_type_id.code == 'internal' and not rec.check_is_pick and not rec.check_is_pack and (
                            rec.group_id or 'PO' in origin or 'RT' in origin):
                rec.is_internal_transfer = True
            else:
                rec.is_internal_transfer = False

    @api.multi
    @api.onchange('picking_type_id')
    def _get_check_is_pick(self):
        for rec in self:
            rec.check_is_pick = False
            rec.check_is_pack = False
            rec.check_is_delivery = False
            if rec.picking_type_id and rec.picking_type_id.sequence_id:
                location_pack_zone = self.env.ref('stock.location_pack_zone')
                stock_location_output = self.env.ref('stock.stock_location_output')
                if 'PICK' in rec.picking_type_id.sequence_id.prefix or rec.picking_type_id.default_location_dest_id == location_pack_zone:
                    rec.check_is_pick = True
                elif 'PACK' in rec.picking_type_id.sequence_id.prefix or rec.picking_type_id.default_location_src_id == location_pack_zone:
                    rec.check_is_pack = True
                elif 'OUT' in rec.picking_type_id.sequence_id.prefix and rec.picking_type_id.default_location_src_id == stock_location_output:
                    rec.check_is_delivery = True

    @api.onchange('product_id')
    def _get_location_domain(self):
        for rec in self:
            if rec.check_is_pick and rec.product_id.location_ids:
                rec.product_location_ids = json.dumps(rec.product_id.location_ids.ids)
            elif rec.picking_type_id and rec.picking_type_id.code == 'incoming' and rec.product_id.location_ids:
                rec.product_location_ids = json.dumps(rec.product_id.location_ids.ids)
            else:
                rec.product_location_ids = json.dumps(rec.env['stock.location'].search([]).ids)

    def get_check_is_internal_transfer(self):
        for rec in self:
            check_is_internal_transfer = False
            origin = rec.picking_id.origin or ''
            if rec.picking_type_id.code == 'internal' and not rec.check_is_pick and not rec.check_is_pack and (
                            rec.group_id or 'PO' in origin or 'RT' in origin):
                rec.is_internal_transfer = True
            else:
                rec.is_internal_transfer = False
            return check_is_internal_transfer


            # @api.onchange('product_id')
            # def get_location_source(self):
            #     for rec in self:
            #         if rec.check_is_pick:
            #             if rec.product_id and rec.product_id.location_ids:
            #                 rec.location_id = rec.product_id.location_ids[0]
            #                 return {'domain' : {'location_id': [('id','in',self.product_id.location_ids.ids)]}}
            #
            #         if rec.picking_type_id and rec.picking_type_id.code == 'incoming':
            #             if rec.product_id and rec.product_id.location_ids:
            #                 rec.location_dest_id = rec.product_id.location_ids[0]

            # @api.model
            # def create(self,val):
            #     res = super(stock_move_ihr, self).create(val)
            #     if not res.location_id or res.location_id not in res.product_id.location_ids:
            #         if res.check_is_pick and not res.picking_id.is_picking_return:
            #             if res.product_id and res.product_id.location_ids:
            #                 res.location_id = res.product_id.location_ids[0]
            #
            #         if res.is_internal_transfer and not res.picking_id.is_picking_return:
            #             if res.product_id and res.product_id.location_ids:
            #                 res.location_dest_id = res.product_id.location_ids[0]
            #     return res


class stock_location_ihr(models.Model):
    _inherit = 'stock.location'

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
    #     args = args or []
    #     if 'move_select_location' in self._context:
    #         if not self._context.get('move_select_location', False):
    #             pass
    #         else:
    #             location_ids = self._context.get('move_select_location', False)
    #             location_ids = json.loads(location_ids)
    #             args.append(('id', 'in', location_ids))
    #     return super(stock_location_ihr, self).name_search(name=name, args=args, operator=operator, limit=limit)
