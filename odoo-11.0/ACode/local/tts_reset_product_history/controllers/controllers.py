# -*- coding: utf-8 -*-
from odoo import http

# class TtsResetProductHistory(http.Controller):
#     @http.route('/tts_reset_product_history/tts_reset_product_history/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_reset_product_history/tts_reset_product_history/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_reset_product_history.listing', {
#             'root': '/tts_reset_product_history/tts_reset_product_history',
#             'objects': http.request.env['tts_reset_product_history.tts_reset_product_history'].search([]),
#         })

#     @http.route('/tts_reset_product_history/tts_reset_product_history/objects/<model("tts_reset_product_history.tts_reset_product_history"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_reset_product_history.object', {
#             'object': obj
#         })