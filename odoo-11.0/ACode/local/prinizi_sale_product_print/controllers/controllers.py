# -*- coding: utf-8 -*-
from odoo import http

# class TtsSaleProductPrint(http.Controller):
#     @http.route('/tts_sale_product_print/tts_sale_product_print/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_sale_product_print/tts_sale_product_print/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_sale_product_print.listing', {
#             'root': '/tts_sale_product_print/tts_sale_product_print',
#             'objects': http.request.env['tts_sale_product_print.tts_sale_product_print'].search([]),
#         })

#     @http.route('/tts_sale_product_print/tts_sale_product_print/objects/<model("tts_sale_product_print.tts_sale_product_print"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_sale_product_print.object', {
#             'object': obj
#         })