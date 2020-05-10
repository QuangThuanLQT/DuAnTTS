# -*- coding: utf-8 -*-
from odoo import http

# class TtsRelatedUser(http.Controller):
#     @http.route('/tts_related_user/tts_related_user/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_related_user/tts_related_user/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_related_user.listing', {
#             'root': '/tts_related_user/tts_related_user',
#             'objects': http.request.env['tts_related_user.tts_related_user'].search([]),
#         })

#     @http.route('/tts_related_user/tts_related_user/objects/<model("tts_related_user.tts_related_user"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_related_user.object', {
#             'object': obj
#         })