# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from datetime import datetime


class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def action_done(self):
        res = super(stock_move, self).action_done()
        for stock in self:
            if stock.inventory_id and stock.inventory_id.accounting_date:
                stock.write({'date': stock.inventory_id.accounting_date})
                for quant in stock.quant_ids:
                    quant.in_date = stock.inventory_id.accounting_date

            order = stock.purchase_order_id or stock.sale_order_id
            if order and stock.state == 'done':
                stock.write({'date': fields.Datetime.now()})

        return res

    @api.multi
    def update_stock_move_date(self):
        location_procurement = self.env.ref('stock.location_procurement')
        stock_location_stock = self.env.ref('stock.stock_location_stock')

        # move_ids = self.env['stock.move'].search(
        #     [('location_id', '=', location_procurement.id), ('location_dest_id', '=', stock_location_stock.id),
        #      ('state', '=', 'done')])
        # move_ids2 = self.env['stock.move'].search([('state', '=', 'done'), ('picking_type_id.code', '=', 'outgoing')])
        # for move in move_ids:
        #     if move.picking_id:
        #         order = move.picking_id.purchase_id or move.picking_id.sale_id
        #         if order:
        #             move.write({
        #                 'date': order.confirmation_date
        #             })
        # for move in move_ids2:
        #     if move.picking_id:
        #         order = move.picking_id.purchase_id or move.picking_id.sale_id
        #         if order:
        #             move.write({
        #                 'date': order.confirmation_date
        #             })
        sale_ids = self.env['sale.order'].search([('sale_order_return', '=', False)])
        for sale in sale_ids:
            for picking in sale.picking_ids:
                if picking.picking_type_code == 'internal':
                    date = False
                    for history in picking.stock_picking_log_ids:
                        list = history.status_changed.split(' -> ')
                        if list[1] == 'Done':
                            date = history.time_log
                    for move in picking.move_lines:
                        if move.state == 'done':
                            if date:
                                move.date = date
                if picking.picking_type_code == 'outgoing':
                    date = False
                    for history in picking.stock_picking_log_ids:
                        list = history.status_changed.split(' -> ')
                        if list[1] == 'Delivering':
                            date = history.time_log
                    for move in picking.move_lines:
                        if move.state == 'done':
                            if date:
                                move.date = date

        sale_return_ids = self.env['sale.order'].search([('sale_order_return', '=', True)])
        for sale in sale_return_ids:
            for picking in sale.picking_ids:
                if picking.picking_type_code == 'internal':
                    date = False
                    for history in picking.stock_picking_log_ids:
                        list = history.status_changed.split(' -> ')
                        if 'Đang kiểm hàng' in list and 'Hoàn thành' in list:
                            date = history.time_log
                    for move in picking.move_lines:
                        if move.state == 'done':
                            if date:
                                move.date = date
                if picking.picking_type_code == 'incoming':
                    date = False
                    for history in picking.stock_picking_log_ids:
                        list = history.status_changed.split(' -> ')
                        if 'Nhận hàng' in list and 'Hoàn thành' in list:
                            date = history.time_log
                    for move in picking.move_lines:
                        if move.state == 'done':
                            if date:
                                move.date = date

        purchase_ids = self.env['purchase.order'].search([('purchase_order_return', '=', False)])
        for purchase in purchase_ids:
            for picking in purchase.picking_ids:
                if picking.picking_type_code == 'internal':
                    date = False
                    for history in picking.stock_picking_log_ids:
                        list = history.status_changed.split(' -> ')
                        if 'Đang kiểm hàng' in list and 'Hoàn thành' in list:
                            date = history.time_log
                    for move in picking.move_lines:
                        if move.state == 'done':
                            if date:
                                move.date = date
                if picking.picking_type_code == 'incoming':
                    date = False
                    for history in picking.stock_picking_log_ids:
                        list = history.status_changed.split(' -> ')
                        if 'Nhận hàng' in list and 'Hoàn thành' in list:
                            date = history.time_log
                    for move in picking.move_lines:
                        if move.state == 'done':
                            if date:
                                move.date = date

        purchase_return_ids = self.env['purchase.order'].search([('purchase_order_return', '=', True)])
        for purchase in purchase_return_ids:
            for picking in purchase.picking_ids:
                if picking.picking_type_code == 'internal':
                    date = False
                    for history in picking.stock_picking_log_ids:
                        list = history.status_changed.split(' -> ')
                        if list[1] == 'Done':
                            date = history.time_log
                    for move in picking.move_lines:
                        if move.state == 'done':
                            if date:
                                move.date = date
                if picking.picking_type_code == 'outgoing':
                    date = False
                    for history in picking.stock_picking_log_ids:
                        list = history.status_changed.split(' -> ')
                        if list[1] == 'Delivering':
                            date = history.time_log
                    for move in picking.move_lines:
                        if move.state == 'done':
                            if date:
                                move.date = date

