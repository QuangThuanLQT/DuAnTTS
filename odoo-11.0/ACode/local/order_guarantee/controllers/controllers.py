# -*- coding: utf-8 -*-
from odoo import http

# class OrderGuarantee(http.Controller):
#     @http.route('/order_guarantee/order_guarantee/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/order_guarantee/order_guarantee/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('order_guarantee.listing', {
#             'root': '/order_guarantee/order_guarantee',
#             'objects': http.request.env['order_guarantee.order_guarantee'].search([]),
#         })

#     @http.route('/order_guarantee/order_guarantee/objects/<model("order_guarantee.order_guarantee"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('order_guarantee.object', {
#             'object': obj
#         })