# -*- coding: utf-8 -*-
from odoo import http

# class TtsModifierLeave(http.Controller):
#     @http.route('/tts_modifier_leave/tts_modifier_leave/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_modifier_leave/tts_modifier_leave/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_modifier_leave.listing', {
#             'root': '/tts_modifier_leave/tts_modifier_leave',
#             'objects': http.request.env['tts_modifier_leave.tts_modifier_leave'].search([]),
#         })

#     @http.route('/tts_modifier_leave/tts_modifier_leave/objects/<model("tts_modifier_leave.tts_modifier_leave"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_modifier_leave.object', {
#             'object': obj
#         })