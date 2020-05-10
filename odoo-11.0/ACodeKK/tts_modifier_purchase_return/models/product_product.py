# -*- coding: utf-8 -*-

from odoo import models, fields, api
import StringIO
import xlsxwriter
from odoo.addons import decimal_precision as dp
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta


class product_product_ihr(models.Model):
    _inherit = 'product.product'

    @api.model
    def execute_query(self, query, get_result=False):
        self.env.cr.execute(query)
        if get_result:
            results = self.env.cr.fetchall()
            return results
        return True

    @api.depends('qty_available', 'virtual_available')
    def _compute_product(self):
        # move_obj = self.env['stock.move'].sudo()
        dest_location = self.env.ref('stock.stock_location_customers')

        for rec in self:
            rec.sp_ban_chua_giao = 0
            rec.sp_da_bao_gia = 0
            rec.sp_co_the_ban = 0

            sp_ban_chua_tao_picking = 0
            sp_ban_chua_giao = 0

            if self._context.get('location', False):
                # sale_order_line = self.env['sale.order.line']
                query = """SELECT 
                    sm.product_id, SUM(sm.product_uom_qty)
                FROM 
                    stock_move sm
                WHERE 
                    sm.product_id = %s 
                    AND sm.location_id = %s 
                    AND (sm.state NOT IN ('done', 'cancel'))
                GROUP BY
                    sm.product_id
                """ % (rec.id, self._context.get('location'))
                query_result = self.execute_query(query, True)
                if query_result and len(query_result) > 0:
                    for query_line in query_result:
                        if query_line[1]:
                            sp_ban_chua_giao = query_line[1]
                # move_cancel_ids = move_obj.search(
                #     [('product_id', '=', rec.id), ('location_id', '=', self._context.get('location', False)),
                #      ('state', '=', 'cancel')])

            else:
                # pass
                # sp_ban_chua_giao = sum(move_obj.search([
                #     ('product_id', '=', rec.id),
                #     ('location_dest_id', '=', dest_location.id or False),
                #     ('state', 'not in', ['done', 'cancel'])
                # ]).mapped('product_uom_qty'))

                query = """SELECT 
                    sm.product_id, SUM(sm.product_uom_qty)
                FROM 
                    stock_move sm
                WHERE 
                    sm.product_id = %s 
                    AND sm.location_dest_id = %s 
                    AND (sm.state NOT IN ('done', 'cancel'))
                GROUP BY
                    sm.product_id
                """ % (rec.id, dest_location.id)
                query_result = self.execute_query(query, True)
                if query_result and len(query_result) > 0:
                    for query_line in query_result:
                        if query_line[1]:
                            sp_ban_chua_giao = query_line[1]

                # move_cancel_ids = move_obj.search(
                #     [('product_id', '=', rec.id), ('location_dest_id', '=', dest_location.id or False),
                #      ('state', '=', 'cancel')])
                # sale_order_line = self.env['sale.order.line'].search([
                #     ('product_id', '=', rec.id),
                #     ('order_id.state', '=', 'sale'),
                #     ('order_id.trang_thai_dh', '=', False)
                # ])

                query = """SELECT 
                    sol.product_id, SUM(sol.product_uom_qty)
                FROM 
                    sale_order_line sol
                INNER JOIN
                    sale_order so
                ON 
                    so.id = sol.order_id
                WHERE 
                    sol.product_id = %s 
                    AND so.state = 'sale' 
                    AND (so.trang_thai_dh IS NULL OR so.trang_thai_dh = '')
                GROUP BY
                    sol.product_id
                """ % (rec.id)
                query_result = self.execute_query(query, True)
                if query_result and len(query_result) > 0:
                    for query_line in query_result:
                        if query_line[1]:
                            sp_ban_chua_tao_picking = query_line[1]

            # sale_cancel_line = self.env['sale.order.line'].search([
            #     ('product_id', '=', rec.id),
            #     ('order_id.trang_thai_dh', '=', 'reverse_tranfer')
            # ])
            sl_ban_huy = 0
            query = """SELECT 
                sol.product_id, SUM(sol.product_uom_qty)
            FROM 
                sale_order_line sol
            INNER JOIN
                sale_order so
            ON 
                so.id = sol.order_id
            WHERE 
                sol.product_id = %s 
                AND so.trang_thai_dh = 'reverse_tranfer'
            GROUP BY
                sol.product_id
            """ % (rec.id)
            query_result = self.execute_query(query, True)
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    if query_line[1]:
                        sl_ban_huy = query_line[1]

            sl_mua_huy = 0
            query = """SELECT 
                pol.product_id, SUM(pol.product_qty)
            FROM 
                purchase_order_line pol
            INNER JOIN
                purchase_order po
            ON 
                po.id = pol.order_id
            WHERE 
                pol.product_id = %s 
                AND po.operation_state = 'reverse_tranfer'
                AND po.purchase_order_return IS TRUE
            GROUP BY
                pol.product_id
            """ % (rec.id)
            query_result = self.execute_query(query, True)
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    if query_line[1]:
                        sl_mua_huy = query_line[1]

            sp_ban_da_huy = sl_ban_huy + sl_mua_huy
            # for move_cancel_id in move_cancel_ids:
            #     if move_cancel_id.picking_id.sale_id and move_cancel_id.picking_id.sale_id.trang_thai_dh == 'reverse_tranfer':
            #         sp_ban_da_huy += move_cancel_id.product_uom_qty
            #     if move_cancel_id.picking_id.purchase_id and move_cancel_id.picking_id.purchase_id.operation_state == 'reverse_tranfer':
            #         sp_ban_da_huy += move_cancel_id.product_uom_qty

            rec.sp_ban_chua_giao = sp_ban_chua_giao + sp_ban_da_huy + sp_ban_chua_tao_picking

            sp_da_bao_gia_ban = 0
            sp_da_bao_gia_mua = 0

            query = """SELECT 
                sol.product_id, SUM(sol.product_uom_qty)
            FROM 
                sale_order_line sol
            INNER JOIN
                sale_order so
            ON 
                so.id = sol.order_id
            WHERE 
                sol.product_id = %s 
                AND so.state IN ('draft', 'sent')
            GROUP BY
                sol.product_id
            """ % (rec.id)
            query_result = self.execute_query(query, True)
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    if query_line[1]:
                        sp_da_bao_gia_ban = query_line[1]

            query = """SELECT 
                pol.product_id, SUM(pol.product_qty)
            FROM 
                purchase_order_line pol
            INNER JOIN
                purchase_order po
            ON 
                po.id = pol.order_id
            WHERE 
                pol.product_id = %s 
                AND po.state IN ('draft', 'sent')
                AND po.purchase_order_return IS TRUE
                AND po.location_return = 'normal'
            GROUP BY
                pol.product_id
            """ % (rec.id)
            query_result = self.execute_query(query, True)
            if query_result and len(query_result) > 0:
                for query_line in query_result:
                    if query_line[1]:
                        sp_da_bao_gia_mua = query_line[1]

            # line_purchase_ids = self.env['purchase.order.line'].search([
            #     ('product_id', '=', rec.id),
            #     ('order_id.state', 'in', ),
            #     ('order_id.purchase_order_return', '=', True),
            #     ('order_id.location_return', '=', 'normal')
            # ])
            sp_da_bao_gia = sp_da_bao_gia_ban + sp_da_bao_gia_mua
            rec.sp_da_bao_gia = sp_da_bao_gia

            rec.sp_co_the_ban = rec.qty_available - rec.sp_ban_chua_giao - rec.sp_da_bao_gia
