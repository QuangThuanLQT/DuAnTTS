# -*- coding: utf-8 -*-
from odoo import http

# class TtsDanangPartner(http.Controller):
#     @http.route('/tts_danang_partner/tts_danang_partner/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_danang_partner/tts_danang_partner/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_danang_partner.listing', {
#             'root': '/tts_danang_partner/tts_danang_partner',
#             'objects': http.request.env['tts_danang_partner.tts_danang_partner'].search([]),
#         })

#     @http.route('/tts_danang_partner/tts_danang_partner/objects/<model("tts_danang_partner.tts_danang_partner"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_danang_partner.object', {
#             'object': obj
#         })