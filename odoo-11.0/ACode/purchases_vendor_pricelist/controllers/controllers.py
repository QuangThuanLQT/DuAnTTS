# -*- coding: utf-8 -*-
from odoo import http

# class PurchasesVendorPricelist(http.Controller):
#     @http.route('/purchases_vendor_pricelist/purchases_vendor_pricelist/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchases_vendor_pricelist/purchases_vendor_pricelist/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchases_vendor_pricelist.listing', {
#             'root': '/purchases_vendor_pricelist/purchases_vendor_pricelist',
#             'objects': http.request.env['purchases_vendor_pricelist.purchases_vendor_pricelist'].search([]),
#         })

#     @http.route('/purchases_vendor_pricelist/purchases_vendor_pricelist/objects/<model("purchases_vendor_pricelist.purchases_vendor_pricelist"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchases_vendor_pricelist.object', {
#             'object': obj
#         })