# -*- coding: utf-8 -*-
from odoo import http

# class TtsSaleConfigCommision(http.Controller):
#     @http.route('/tts_sale_config_commision/tts_sale_config_commision/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_sale_config_commision/tts_sale_config_commision/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_sale_config_commision.listing', {
#             'root': '/tts_sale_config_commision/tts_sale_config_commision',
#             'objects': http.request.env['tts_sale_config_commision.tts_sale_config_commision'].search([]),
#         })

#     @http.route('/tts_sale_config_commision/tts_sale_config_commision/objects/<model("tts_sale_config_commision.tts_sale_config_commision"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_sale_config_commision.object', {
#             'object': obj
#         })