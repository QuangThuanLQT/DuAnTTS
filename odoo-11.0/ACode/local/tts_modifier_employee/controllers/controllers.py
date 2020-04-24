# -*- coding: utf-8 -*-
from odoo import http

# class TtsModifierEmployee(http.Controller):
#     @http.route('/tts_modifier_employee/tts_modifier_employee/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_modifier_employee/tts_modifier_employee/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_modifier_employee.listing', {
#             'root': '/tts_modifier_employee/tts_modifier_employee',
#             'objects': http.request.env['tts_modifier_employee.tts_modifier_employee'].search([]),
#         })

#     @http.route('/tts_modifier_employee/tts_modifier_employee/objects/<model("tts_modifier_employee.tts_modifier_employee"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_modifier_employee.object', {
#             'object': obj
#         })