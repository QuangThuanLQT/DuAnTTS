# -*- coding: utf-8 -*-
from odoo import http

# class TtsMultiWarehouse(http.Controller):
#     @http.route('/tts_multi_warehouse/tts_multi_warehouse/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_multi_warehouse/tts_multi_warehouse/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_multi_warehouse.listing', {
#             'root': '/tts_multi_warehouse/tts_multi_warehouse',
#             'objects': http.request.env['tts_multi_warehouse.tts_multi_warehouse'].search([]),
#         })

#     @http.route('/tts_multi_warehouse/tts_multi_warehouse/objects/<model("tts_multi_warehouse.tts_multi_warehouse"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_multi_warehouse.object', {
#             'object': obj
#         })