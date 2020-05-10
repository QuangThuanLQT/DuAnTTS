# -*- coding: utf-8 -*-
from odoo import http

# class Generate2dBarcode(http.Controller):
#     @http.route('/generate_2d_barcode/generate_2d_barcode/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/generate_2d_barcode/generate_2d_barcode/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('generate_2d_barcode.listing', {
#             'root': '/generate_2d_barcode/generate_2d_barcode',
#             'objects': http.request.env['generate_2d_barcode.generate_2d_barcode'].search([]),
#         })

#     @http.route('/generate_2d_barcode/generate_2d_barcode/objects/<model("generate_2d_barcode.generate_2d_barcode"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('generate_2d_barcode.object', {
#             'object': obj
#         })