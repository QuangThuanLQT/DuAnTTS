# -*- coding: utf-8 -*-
from odoo import http

# class SaleInventory(http.Controller):
#     @http.route('/sale_inventory/sale_inventory/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_inventory/sale_inventory/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_inventory.listing', {
#             'root': '/sale_inventory/sale_inventory',
#             'objects': http.request.env['sale_inventory.sale_inventory'].search([]),
#         })

#     @http.route('/sale_inventory/sale_inventory/objects/<model("sale_inventory.sale_inventory"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_inventory.object', {
#             'object': obj
#         })