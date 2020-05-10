# -*- coding: utf-8 -*-
from odoo import http

# class ProductTree2(http.Controller):
#     @http.route('/product_tree2/product_tree2/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_tree2/product_tree2/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_tree2.listing', {
#             'root': '/product_tree2/product_tree2',
#             'objects': http.request.env['product_tree2.product_tree2'].search([]),
#         })

#     @http.route('/product_tree2/product_tree2/objects/<model("product_tree2.product_tree2"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_tree2.object', {
#             'object': obj
#         })