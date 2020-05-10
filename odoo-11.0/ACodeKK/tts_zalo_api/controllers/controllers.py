# -*- coding: utf-8 -*-
from odoo import http

# class TtsZaloApi(http.Controller):
#     @http.route('/tts_zalo_api/tts_zalo_api/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_zalo_api/tts_zalo_api/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_zalo_api.listing', {
#             'root': '/tts_zalo_api/tts_zalo_api',
#             'objects': http.request.env['tts_zalo_api.tts_zalo_api'].search([]),
#         })

#     @http.route('/tts_zalo_api/tts_zalo_api/objects/<model("tts_zalo_api.tts_zalo_api"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_zalo_api.object', {
#             'object': obj
#         })