# -*- coding: utf-8 -*-
from odoo import http

# class TuanhuyPurchaseSettingBarcode(http.Controller):
#     @http.route('/tuanhuy_purchase_setting_barcode/tuanhuy_purchase_setting_barcode/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tuanhuy_purchase_setting_barcode/tuanhuy_purchase_setting_barcode/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tuanhuy_purchase_setting_barcode.listing', {
#             'root': '/tuanhuy_purchase_setting_barcode/tuanhuy_purchase_setting_barcode',
#             'objects': http.request.env['tuanhuy_purchase_setting_barcode.tuanhuy_purchase_setting_barcode'].search([]),
#         })

#     @http.route('/tuanhuy_purchase_setting_barcode/tuanhuy_purchase_setting_barcode/objects/<model("tuanhuy_purchase_setting_barcode.tuanhuy_purchase_setting_barcode"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tuanhuy_purchase_setting_barcode.object', {
#             'object': obj
#         })