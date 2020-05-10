# -*- coding: utf-8 -*-
from odoo import http

# class StockPickingToPurchaseRequest(http.Controller):
#     @http.route('/stock_picking_to_purchase_request/stock_picking_to_purchase_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stock_picking_to_purchase_request/stock_picking_to_purchase_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('stock_picking_to_purchase_request.listing', {
#             'root': '/stock_picking_to_purchase_request/stock_picking_to_purchase_request',
#             'objects': http.request.env['stock_picking_to_purchase_request.stock_picking_to_purchase_request'].search([]),
#         })

#     @http.route('/stock_picking_to_purchase_request/stock_picking_to_purchase_request/objects/<model("stock_picking_to_purchase_request.stock_picking_to_purchase_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stock_picking_to_purchase_request.object', {
#             'object': obj
#         })