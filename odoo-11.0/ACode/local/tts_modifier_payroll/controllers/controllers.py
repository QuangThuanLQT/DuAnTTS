# -*- coding: utf-8 -*-
from odoo import http

# class TtsModifierPayroll(http.Controller):
#     @http.route('/tts_modifier_payroll/tts_modifier_payroll/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_modifier_payroll/tts_modifier_payroll/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_modifier_payroll.listing', {
#             'root': '/tts_modifier_payroll/tts_modifier_payroll',
#             'objects': http.request.env['tts_modifier_payroll.tts_modifier_payroll'].search([]),
#         })

#     @http.route('/tts_modifier_payroll/tts_modifier_payroll/objects/<model("tts_modifier_payroll.tts_modifier_payroll"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_modifier_payroll.object', {
#             'object': obj
#         })