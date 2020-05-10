# -*- coding: utf-8 -*-
from odoo import http

# class TtsModifierVendor(http.Controller):
#     @http.route('/tts_modifier_vendor/tts_modifier_vendor/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_modifier_vendor/tts_modifier_vendor/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_modifier_vendor.listing', {
#             'root': '/tts_modifier_vendor/tts_modifier_vendor',
#             'objects': http.request.env['tts_modifier_vendor.tts_modifier_vendor'].search([]),
#         })

#     @http.route('/tts_modifier_vendor/tts_modifier_vendor/objects/<model("tts_modifier_vendor.tts_modifier_vendor"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_modifier_vendor.object', {
#             'object': obj
#         })