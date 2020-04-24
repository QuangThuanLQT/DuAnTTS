# -*- coding: utf-8 -*-
from odoo import http

# class ModifierSaleDiscountTotal(http.Controller):
#     @http.route('/modifier_sale_discount_total/modifier_sale_discount_total/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/modifier_sale_discount_total/modifier_sale_discount_total/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('modifier_sale_discount_total.listing', {
#             'root': '/modifier_sale_discount_total/modifier_sale_discount_total',
#             'objects': http.request.env['modifier_sale_discount_total.modifier_sale_discount_total'].search([]),
#         })

#     @http.route('/modifier_sale_discount_total/modifier_sale_discount_total/objects/<model("modifier_sale_discount_total.modifier_sale_discount_total"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('modifier_sale_discount_total.object', {
#             'object': obj
#         })