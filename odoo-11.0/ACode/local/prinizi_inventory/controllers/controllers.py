# -*- coding: utf-8 -*-
from odoo import http

# class PriniziInventory(http.Controller):
#     @http.route('/prinizi_inventory/prinizi_inventory/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/prinizi_inventory/prinizi_inventory/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('prinizi_inventory.listing', {
#             'root': '/prinizi_inventory/prinizi_inventory',
#             'objects': http.request.env['prinizi_inventory.prinizi_inventory'].search([]),
#         })

#     @http.route('/prinizi_inventory/prinizi_inventory/objects/<model("prinizi_inventory.prinizi_inventory"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('prinizi_inventory.object', {
#             'object': obj
#         })