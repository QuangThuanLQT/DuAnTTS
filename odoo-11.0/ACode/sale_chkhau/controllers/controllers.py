# -*- coding: utf-8 -*-
from odoo import http

# class SaleChkhau(http.Controller):
#     @http.route('/sale_chkhau/sale_chkhau/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_chkhau/sale_chkhau/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_chkhau.listing', {
#             'root': '/sale_chkhau/sale_chkhau',
#             'objects': http.request.env['sale_chkhau.sale_chkhau'].search([]),
#         })

#     @http.route('/sale_chkhau/sale_chkhau/objects/<model("sale_chkhau.sale_chkhau"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_chkhau.object', {
#             'object': obj
#         })