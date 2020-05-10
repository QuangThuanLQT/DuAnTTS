# -*- coding: utf-8 -*-
from odoo import http

# class SaleProductGroupSale(http.Controller):
#     @http.route('/sale__product__group__sale/sale__product__group__sale/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale__product__group__sale/sale__product__group__sale/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale__product__group__sale.listing', {
#             'root': '/sale__product__group__sale/sale__product__group__sale',
#             'objects': http.request.env['sale__product__group__sale.sale__product__group__sale'].search([]),
#         })

#     @http.route('/sale__product__group__sale/sale__product__group__sale/objects/<model("sale__product__group__sale.sale__product__group__sale"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale__product__group__sale.object', {
#             'object': obj
#         })