# -*- coding: utf-8 -*-
from odoo import http

# class PriniziMergeSaleOrder(http.Controller):
#     @http.route('/prinizi_merge_sale_order/prinizi_merge_sale_order/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/prinizi_merge_sale_order/prinizi_merge_sale_order/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('prinizi_merge_sale_order.listing', {
#             'root': '/prinizi_merge_sale_order/prinizi_merge_sale_order',
#             'objects': http.request.env['prinizi_merge_sale_order.prinizi_merge_sale_order'].search([]),
#         })

#     @http.route('/prinizi_merge_sale_order/prinizi_merge_sale_order/objects/<model("prinizi_merge_sale_order.prinizi_merge_sale_order"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('prinizi_merge_sale_order.object', {
#             'object': obj
#         })