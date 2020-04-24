# -*- coding: utf-8 -*-

from odoo import models, fields, api
# from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
# from datetime import datetime

class update_amount_stock(models.TransientModel):
    _name = 'update.amount.stock'

    start_date = fields.Date(String='Start Date', required=True)
    end_date = fields.Date(String='End Date')

    def update_amount_stock(self):
        conditions = []
        conditions_po_rt = []
        conditions_so_rt_have_so = []
        conditions_so_rt_not_so = []
        conditions_pk_assign = []
        if self.start_date:
            conditions.append(('min_date', '>=', self.start_date))
            conditions_so_rt_have_so.append(('date_order', '>=', self.start_date))
            conditions_so_rt_not_so.append(('date_order', '>=', self.start_date))
            conditions_po_rt.append(('date_order', '>=', self.start_date))
            conditions_pk_assign.append(('min_date', '>=', self.start_date))
        if self.end_date:
            conditions.append(('min_date', '<=', self.end_date))
            conditions_so_rt_have_so.append(('date_order', '<=', self.end_date))
            conditions_so_rt_not_so.append(('date_order', '<=', self.end_date))
            conditions_po_rt.append(('date_order', '<=', self.end_date))
            conditions_pk_assign.append(('min_date', '<=', self.end_date))
        location_stock = self.env.ref('stock.stock_location_stock').id

        # TODO PICKING PO RETURN
        conditions_po_rt.append(('purchase_order_return','=',True))
        picking_po_return_ids = self.env['purchase.order'].search(conditions_po_rt).mapped('picking_ids')
        picking_po_return_ids = self.env['stock.picking'].search([('id','in',picking_po_return_ids.ids),('state','=','done')],order="min_date asc")

        # TODO PICKING SO RETURN
        conditions_so_rt_have_so.append(('sale_order_return','=',True))
        conditions_so_rt_have_so.append(('sale_order_return_ids','!=',False))
        so_rt_have_so = self.env['sale.order'].search(conditions_so_rt_have_so)
        picking_so_rt_have_so_ids = so_rt_have_so.mapped('picking_ids')
        picking_so_rt_have_so_ids = self.env['stock.picking'].search([('id','in',picking_so_rt_have_so_ids.ids),('state','=','done')],order="min_date asc")

        # TODO PICKING SO HAVE RETURN
        picking_so_have_return_ids = so_rt_have_so.mapped('sale_order_return_ids').mapped('picking_ids')
        picking_so_have_return_ids = self.env['stock.picking'].search(
            [('id', 'in', picking_so_have_return_ids.ids), ('state', '=', 'done')], order="min_date asc")

        # TODO PICKING SO NOT HAVE RETURN
        conditions.append(('location_dest_id', '=', location_stock))
        conditions.append(('state','=','done'))
        picking_so_not_have_return_ids = self.env['stock.picking'].search(conditions,order="min_date asc")
        picking_so_not_have_return_ids = picking_so_not_have_return_ids - picking_po_return_ids - picking_so_rt_have_so_ids

        # TODO PICKING ASSIGN
        conditions_pk_assign.append(('state','in',['assigned','partially_available']))
        picking_assign_ids = self.env['stock.picking'].search(conditions_pk_assign,order="min_date asc")

        # TODO RESET ALL PICKING
        for picking_id in (picking_po_return_ids + picking_so_rt_have_so_ids + picking_so_not_have_return_ids):
            picking_id.do_reset_stock_picking()
        for picking_in_id in picking_so_have_return_ids:
            picking_in_id.do_reset_stock_picking()

        # TODO PICKING PO RETURN CONFIRM
        for picking_po_return_id in picking_po_return_ids:
            picking_po_return_id.action_confirm()
            picking_po_return_id.action_assign()
            if picking_po_return_id.state == 'assigned':
                stock_transfer_obj = self.env['stock.immediate.transfer']
                stock_transfer_obj.create(stock_transfer_obj.with_context(
                    {'active_id': picking_po_return_id.id}).default_get(stock_transfer_obj._fields)).process()

        # TODO PICKING SO HAVE RETURN CONFIRM
        for picking_so_have_return_id in picking_so_have_return_ids:
            picking_so_have_return_id.action_confirm()
            picking_so_have_return_id.action_assign()
            if picking_so_have_return_id.state == 'assigned':
                stock_transfer_obj = self.env['stock.immediate.transfer']
                stock_transfer_obj.create(stock_transfer_obj.with_context(
                    {'active_id': picking_so_have_return_id.id}).default_get(stock_transfer_obj._fields)).process()

        # TODO PICKING SO RETURN CONFIRM
        for picking_so_rt_have_so_id in picking_so_rt_have_so_ids:
            picking_so_rt_have_so_id.action_confirm()
            picking_so_rt_have_so_id.action_assign()
            if picking_so_rt_have_so_id.state == 'assigned':
                stock_transfer_obj = self.env['stock.immediate.transfer']
                stock_transfer_obj.create(stock_transfer_obj.with_context(
                    {'active_id': picking_so_rt_have_so_id.id}).default_get(stock_transfer_obj._fields)).process()

        # TODO PICKING SO NOT HAVE RETURN CONFIRM
        for picking_so_not_have_return_id in picking_so_not_have_return_ids:
            picking_so_not_have_return_id.action_confirm()
            picking_so_not_have_return_id.action_assign()
            if picking_so_not_have_return_id.state == 'assigned':
                stock_transfer_obj = self.env['stock.immediate.transfer']
                stock_transfer_obj.create(stock_transfer_obj.with_context(
                    {'active_id': picking_so_not_have_return_id.id}).default_get(stock_transfer_obj._fields)).process()

        # TODO PICKING ASSIGN DO UNRESERVE
        for picking_assign_id in picking_assign_ids:
            picking_assign_id.do_unreserve()
            picking_assign_id.action_assign()


    def update_min_date_picking(self):
        picking_ids = self.env['stock.picking'].search([('min_date', '=', False)])
        for picking_id in picking_ids:
            origin_id = self.env['sale.order'].search([('name','=',picking_id.origin)])
            if origin_id:
                picking_id.min_date = origin_id.date_order
            else:
                origin_id = self.env['purchase.order'].search([('name', '=', picking_id.origin)])
                if origin_id:
                    picking_id.min_date = origin_id.date_order

