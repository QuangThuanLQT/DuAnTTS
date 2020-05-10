# -*- coding: utf-8 -*-
from odoo import http

# class TtsModifierAccessRight(http.Controller):
#     @http.route('/tts_modifier_access_right/tts_modifier_access_right/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_modifier_access_right/tts_modifier_access_right/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_modifier_access_right.listing', {
#             'root': '/tts_modifier_access_right/tts_modifier_access_right',
#             'objects': http.request.env['tts_modifier_access_right.tts_modifier_access_right'].search([]),
#         })

#     @http.route('/tts_modifier_access_right/tts_modifier_access_right/objects/<model("tts_modifier_access_right.tts_modifier_access_right"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_modifier_access_right.object', {
#             'object': obj
#         })