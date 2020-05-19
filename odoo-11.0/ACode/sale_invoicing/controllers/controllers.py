# -*- coding: utf-8 -*-
from odoo import http

# class SaleInvoicing(http.Controller):
#     @http.route('/sale_invoicing/sale_invoicing/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_invoicing/sale_invoicing/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_invoicing.listing', {
#             'root': '/sale_invoicing/sale_invoicing',
#             'objects': http.request.env['sale_invoicing.sale_invoicing'].search([]),
#         })

#     @http.route('/sale_invoicing/sale_invoicing/objects/<model("sale_invoicing.sale_invoicing"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_invoicing.object', {
#             'object': obj
#         })