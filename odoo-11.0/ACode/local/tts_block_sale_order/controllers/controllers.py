# -*- coding: utf-8 -*-
from odoo import http

# class TtsBlockSaleOrder(http.Controller):
#     @http.route('/tts_block_sale_order/tts_block_sale_order/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_block_sale_order/tts_block_sale_order/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_block_sale_order.listing', {
#             'root': '/tts_block_sale_order/tts_block_sale_order',
#             'objects': http.request.env['tts_block_sale_order.tts_block_sale_order'].search([]),
#         })

#     @http.route('/tts_block_sale_order/tts_block_sale_order/objects/<model("tts_block_sale_order.tts_block_sale_order"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_block_sale_order.object', {
#             'object': obj
#         })