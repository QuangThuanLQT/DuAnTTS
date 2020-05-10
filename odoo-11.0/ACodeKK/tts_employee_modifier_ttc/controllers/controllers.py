# -*- coding: utf-8 -*-
from odoo import http

# class TtsEmployeeModifierTtc(http.Controller):
#     @http.route('/tts_employee_modifier_ttc/tts_employee_modifier_ttc/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_employee_modifier_ttc/tts_employee_modifier_ttc/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_employee_modifier_ttc.listing', {
#             'root': '/tts_employee_modifier_ttc/tts_employee_modifier_ttc',
#             'objects': http.request.env['tts_employee_modifier_ttc.tts_employee_modifier_ttc'].search([]),
#         })

#     @http.route('/tts_employee_modifier_ttc/tts_employee_modifier_ttc/objects/<model("tts_employee_modifier_ttc.tts_employee_modifier_ttc"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_employee_modifier_ttc.object', {
#             'object': obj
#         })