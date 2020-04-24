# -*- coding: utf-8 -*-
from odoo import http

# class TtsDanangProduct(http.Controller):
#     @http.route('/tts_danang_product/tts_danang_product/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_danang_product/tts_danang_product/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_danang_product.listing', {
#             'root': '/tts_danang_product/tts_danang_product',
#             'objects': http.request.env['tts_danang_product.tts_danang_product'].search([]),
#         })

#     @http.route('/tts_danang_product/tts_danang_product/objects/<model("tts_danang_product.tts_danang_product"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_danang_product.object', {
#             'object': obj
#         })