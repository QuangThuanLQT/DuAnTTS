# -*- coding: utf-8 -*-
from odoo import http

# class TtsAttandanceCheckinOut(http.Controller):
#     @http.route('/tts_attandance_checkin_out/tts_attandance_checkin_out/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_attandance_checkin_out/tts_attandance_checkin_out/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_attandance_checkin_out.listing', {
#             'root': '/tts_attandance_checkin_out/tts_attandance_checkin_out',
#             'objects': http.request.env['tts_attandance_checkin_out.tts_attandance_checkin_out'].search([]),
#         })

#     @http.route('/tts_attandance_checkin_out/tts_attandance_checkin_out/objects/<model("tts_attandance_checkin_out.tts_attandance_checkin_out"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_attandance_checkin_out.object', {
#             'object': obj
#         })