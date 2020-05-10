# -*- coding: utf-8 -*-
from odoo import http

# class TtsApi(http.Controller):
#     @http.route('/tts_api/tts_api/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_api/tts_api/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_api.listing', {
#             'root': '/tts_api/tts_api',
#             'objects': http.request.env['tts_api.tts_api'].search([]),
#         })

#     @http.route('/tts_api/tts_api/objects/<model("tts_api.tts_api"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_api.object', {
#             'object': obj
#         })