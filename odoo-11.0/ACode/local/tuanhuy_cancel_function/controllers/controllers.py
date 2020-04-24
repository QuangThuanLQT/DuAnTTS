# -*- coding: utf-8 -*-
from odoo import http

# class TuanhuyCancelFunction(http.Controller):
#     @http.route('/tuanhuy_cancel_function/tuanhuy_cancel_function/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tuanhuy_cancel_function/tuanhuy_cancel_function/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tuanhuy_cancel_function.listing', {
#             'root': '/tuanhuy_cancel_function/tuanhuy_cancel_function',
#             'objects': http.request.env['tuanhuy_cancel_function.tuanhuy_cancel_function'].search([]),
#         })

#     @http.route('/tuanhuy_cancel_function/tuanhuy_cancel_function/objects/<model("tuanhuy_cancel_function.tuanhuy_cancel_function"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tuanhuy_cancel_function.object', {
#             'object': obj
#         })