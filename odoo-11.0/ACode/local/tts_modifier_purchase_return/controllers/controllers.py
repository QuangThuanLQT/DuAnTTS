# -*- coding: utf-8 -*-
from odoo import http

# class TtsModifierPurchaseReturn(http.Controller):
#     @http.route('/tts_modifier_purchase_return/tts_modifier_purchase_return/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_modifier_purchase_return/tts_modifier_purchase_return/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_modifier_purchase_return.listing', {
#             'root': '/tts_modifier_purchase_return/tts_modifier_purchase_return',
#             'objects': http.request.env['tts_modifier_purchase_return.tts_modifier_purchase_return'].search([]),
#         })

#     @http.route('/tts_modifier_purchase_return/tts_modifier_purchase_return/objects/<model("tts_modifier_purchase_return.tts_modifier_purchase_return"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_modifier_purchase_return.object', {
#             'object': obj
#         })