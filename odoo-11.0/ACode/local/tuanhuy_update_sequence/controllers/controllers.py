# -*- coding: utf-8 -*-
from odoo import http

# class TuanhuyUpdateSequence(http.Controller):
#     @http.route('/tuanhuy_update_sequence/tuanhuy_update_sequence/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tuanhuy_update_sequence/tuanhuy_update_sequence/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tuanhuy_update_sequence.listing', {
#             'root': '/tuanhuy_update_sequence/tuanhuy_update_sequence',
#             'objects': http.request.env['tuanhuy_update_sequence.tuanhuy_update_sequence'].search([]),
#         })

#     @http.route('/tuanhuy_update_sequence/tuanhuy_update_sequence/objects/<model("tuanhuy_update_sequence.tuanhuy_update_sequence"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tuanhuy_update_sequence.object', {
#             'object': obj
#         })