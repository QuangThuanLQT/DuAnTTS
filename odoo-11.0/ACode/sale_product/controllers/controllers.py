# -*- coding: utf-8 -*-
from odoo import http

# class SaleProduct(http.Controller):
#     @http.route('/sale_product/sale_product/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_product/sale_product/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_product.listing', {
#             'root': '/sale_product/sale_product',
#             'objects': http.request.env['sale_product.sale_product'].search([]),
#         })

#     @http.route('/sale_product/sale_product/objects/<model("sale_product.sale_product"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_product.object', {
#             'object': obj
#         })