# -*- coding: utf-8 -*-
from odoo import http

# class TtsSalePurchaseLog(http.Controller):
#     @http.route('/tts_sale_purchase_log/tts_sale_purchase_log/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_sale_purchase_log/tts_sale_purchase_log/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_sale_purchase_log.listing', {
#             'root': '/tts_sale_purchase_log/tts_sale_purchase_log',
#             'objects': http.request.env['tts_sale_purchase_log.tts_sale_purchase_log'].search([]),
#         })

#     @http.route('/tts_sale_purchase_log/tts_sale_purchase_log/objects/<model("tts_sale_purchase_log.tts_sale_purchase_log"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_sale_purchase_log.object', {
#             'object': obj
#         })