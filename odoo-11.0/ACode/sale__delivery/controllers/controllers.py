# -*- coding: utf-8 -*-
from odoo import http

# class SaleDelivery(http.Controller):
#     @http.route('/sale__delivery/sale__delivery/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale__delivery/sale__delivery/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale__delivery.listing', {
#             'root': '/sale__delivery/sale__delivery',
#             'objects': http.request.env['sale__delivery.sale__delivery'].search([]),
#         })

#     @http.route('/sale__delivery/sale__delivery/objects/<model("sale__delivery.sale__delivery"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale__delivery.object', {
#             'object': obj
#         })