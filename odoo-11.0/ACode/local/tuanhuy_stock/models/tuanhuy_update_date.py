from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round, float_is_zero


class stock_update_Date(models.Model):
    _name = 'stock.update.date'

    start_date = fields.Date(required=True)
    end_date = fields.Date()
    type = fields.Selection([
        ('sale.order','SO'),
        ('purchase.order','PO')], 'Type', required=True)

    # def _cron_update_date_move_line(self):
    #     self.env.cr.execute("SELECT sp.id, sm.id "
    #                         "FROM public.stock_picking as sp LEFT JOIN stock_move as sm ON sp.id = sm.picking_id where sp.date != sm.date;")
    #     res_trans = self.env.cr.fetchall()
    #     for line in res_trans:
    #         if line[1]:
    #             stock_move_id = self.env['stock.move'].browse(line[1])
    #             stock_move_id.date = stock_move_id.picking_id.date


    def action_update_date(self):
        if self.type == 'sale.order':
            domain = []
            if self.start_date:
                domain.append(('date_order', '>=', self.start_date))
            if self.end_date:
                domain.append(('date_order', '<=', self.end_date))
            domain.append(('state', 'not in', ['draft', 'cancel']))

            order_ids = self.env['sale.order'].search(domain)
            for order in order_ids:
                for pick in order.picking_ids:
                    if order.date_order != pick.min_date:
                        pick.min_date = order.date_order

                    for move in pick.move_lines:
                        if move.date != order.date_order:
                            move.date = order.date_order
                        # for quant in move.quant_ids:
                        #     if quant.in_date != order.date_order:
                        #         quant.in_date = order.date_order
            print 'Done'
        elif self.type == 'purchase.order':
            domain = []
            if self.start_date:
                domain.append(('date_order', '>=', self.start_date))
            if self.end_date:
                domain.append(('date_order', '<=', self.end_date))
            domain.append(('state', 'not in', ['draft', 'cancel']))

            order_ids = self.env['purchase.order'].search(domain)
            for order in order_ids:
                for pick in order.picking_ids:
                    if order.date_order != pick.min_date:
                        pick.min_date = order.date_order

                    for move in pick.move_lines:
                        if move.date != order.date_order:
                            move.date = order.date_order
                        # for quant in move.quant_ids:
                        #     if quant.in_date != order.date_order:
                        #         quant.in_date = order.date_order
            print 'Done'
        # else:
        #     domain = []
        #     if self.start_date:
        #         domain.append(('date_order', '>=', self.start_date))
        #     if self.end_date:
        #         domain.append(('date_order', '<=', self.end_date))
        #     domain.append(('state', 'not in', ['draft', 'cancel']))
        #
        #     self.env.cr.execute("SELECT sp.id, sm.id "
        #                         "FROM public.stock_picking as sp LEFT JOIN stock_move as sm ON sp.id = sm.picking_id where sp.date != sm.date;")
        #     res_trans = self.env.cr.fetchall()
        #     for line in res_trans:
        #         if line[1]:
        #             stock_move_id = self.env['stock.move'].browse(line[1])
        #             stock_move_id.date = stock_move_id.picking_id.date

            # order_ids = self.env['sale.order'].search(domain)
            # for order in order_ids:
            #     for pick in order.picking_ids:
            #         if order.date_order != pick.min_date:
            #             pick.min_date = order.date_order
            #
            #         for move in pick.move_lines:
            #             if move.date != order.date_order:
            #                 move.date = order.date_order
            #
            # purchase_order_ids = self.env['purchase.order'].search(domain)
            # for order in purchase_order_ids:
            #     for pick in order.picking_ids:
            #         if order.date_order != pick.min_date:
            #             pick.min_date = order.date_order
            #
            #         for move in pick.move_lines:
            #             if move.date != order.date_order:
            #                 move.date = order.date_order



