# -*- coding: utf-8 -*-
from odoo import http

# class SaleCustomers(http.Controller):
#     @http.route('/sale_customers/sale_customers/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_customers/sale_customers/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_customers.listing', {
#             'root': '/sale_customers/sale_customers',
#             'objects': http.request.env['sale_customers.sale_customers'].search([]),
#         })

#     @http.route('/sale_customers/sale_customers/objects/<model("sale_customers.sale_customers"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_customers.object', {
#             'object': obj
#         })