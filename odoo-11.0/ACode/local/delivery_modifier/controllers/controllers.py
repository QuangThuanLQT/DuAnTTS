# -*- coding: utf-8 -*-
from odoo import http

# class DeliveryModifier(http.Controller):
#     @http.route('/delivery_modifier/delivery_modifier/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/delivery_modifier/delivery_modifier/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('delivery_modifier.listing', {
#             'root': '/delivery_modifier/delivery_modifier',
#             'objects': http.request.env['delivery_modifier.delivery_modifier'].search([]),
#         })

#     @http.route('/delivery_modifier/delivery_modifier/objects/<model("delivery_modifier.delivery_modifier"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('delivery_modifier.object', {
#             'object': obj
#         })