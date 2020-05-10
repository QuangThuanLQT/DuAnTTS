# -*- coding: utf-8 -*-
from odoo import http

# class TuanhuyPurchaseDiscountTotal(http.Controller):
#     @http.route('/tuanhuy_purchase_discount_total/tuanhuy_purchase_discount_total/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tuanhuy_purchase_discount_total/tuanhuy_purchase_discount_total/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tuanhuy_purchase_discount_total.listing', {
#             'root': '/tuanhuy_purchase_discount_total/tuanhuy_purchase_discount_total',
#             'objects': http.request.env['tuanhuy_purchase_discount_total.tuanhuy_purchase_discount_total'].search([]),
#         })

#     @http.route('/tuanhuy_purchase_discount_total/tuanhuy_purchase_discount_total/objects/<model("tuanhuy_purchase_discount_total.tuanhuy_purchase_discount_total"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tuanhuy_purchase_discount_total.object', {
#             'object': obj
#         })