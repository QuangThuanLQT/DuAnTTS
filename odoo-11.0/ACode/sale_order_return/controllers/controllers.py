# -*- coding: utf-8 -*-
from odoo import http

# class SaleOrderReturn(http.Controller):
#     @http.route('/sale_order_return/sale_order_return/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_order_return/sale_order_return/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_order_return.listing', {
#             'root': '/sale_order_return/sale_order_return',
#             'objects': http.request.env['sale_order_return.sale_order_return'].search([]),
#         })

#     @http.route('/sale_order_return/sale_order_return/objects/<model("sale_order_return.sale_order_return"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_order_return.object', {
#             'object': obj
#         })