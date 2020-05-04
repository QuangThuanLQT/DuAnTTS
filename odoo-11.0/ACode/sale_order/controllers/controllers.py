# -*- coding: utf-8 -*-
from odoo import http

# class SaleOrder(http.Controller):
#     @http.route('/sale_order/sale_order/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_order/sale_order/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_order.listing', {
#             'root': '/sale_order/sale_order',
#             'objects': http.request.env['sale_order.sale_order'].search([]),
#         })

#     @http.route('/sale_order/sale_order/objects/<model("sale_order.sale_order"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_order.object', {
#             'object': obj
#         })