# -*- coding: utf-8 -*-
from odoo import http

# class SaleMenu(http.Controller):
#     @http.route('/sale_menu/sale_menu/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_menu/sale_menu/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_menu.listing', {
#             'root': '/sale_menu/sale_menu',
#             'objects': http.request.env['sale_menu.sale_menu'].search([]),
#         })

#     @http.route('/sale_menu/sale_menu/objects/<model("sale_menu.sale_menu"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_menu.object', {
#             'object': obj
#         })