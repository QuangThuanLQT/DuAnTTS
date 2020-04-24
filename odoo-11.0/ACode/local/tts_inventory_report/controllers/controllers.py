# -*- coding: utf-8 -*-
from odoo import http

# class TtsInventoryReport(http.Controller):
#     @http.route('/tts_inventory_report/tts_inventory_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_inventory_report/tts_inventory_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_inventory_report.listing', {
#             'root': '/tts_inventory_report/tts_inventory_report',
#             'objects': http.request.env['tts_inventory_report.tts_inventory_report'].search([]),
#         })

#     @http.route('/tts_inventory_report/tts_inventory_report/objects/<model("tts_inventory_report.tts_inventory_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_inventory_report.object', {
#             'object': obj
#         })