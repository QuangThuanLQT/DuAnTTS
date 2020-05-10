# -*- coding: utf-8 -*-
from odoo import http

# class TuanhuyImportSalePurchase(http.Controller):
#     @http.route('/tuanhuy_import_sale_purchase/tuanhuy_import_sale_purchase/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tuanhuy_import_sale_purchase/tuanhuy_import_sale_purchase/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tuanhuy_import_sale_purchase.listing', {
#             'root': '/tuanhuy_import_sale_purchase/tuanhuy_import_sale_purchase',
#             'objects': http.request.env['tuanhuy_import_sale_purchase.tuanhuy_import_sale_purchase'].search([]),
#         })

#     @http.route('/tuanhuy_import_sale_purchase/tuanhuy_import_sale_purchase/objects/<model("tuanhuy_import_sale_purchase.tuanhuy_import_sale_purchase"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tuanhuy_import_sale_purchase.object', {
#             'object': obj
#         })