# -*- coding: utf-8 -*-
from odoo import http

# class TuanhuyMrp(http.Controller):
#     @http.route('/tuanhuy_mrp/tuanhuy_mrp/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tuanhuy_mrp/tuanhuy_mrp/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tuanhuy_mrp.listing', {
#             'root': '/tuanhuy_mrp/tuanhuy_mrp',
#             'objects': http.request.env['tuanhuy_mrp.tuanhuy_mrp'].search([]),
#         })

#     @http.route('/tuanhuy_mrp/tuanhuy_mrp/objects/<model("tuanhuy_mrp.tuanhuy_mrp"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tuanhuy_mrp.object', {
#             'object': obj
#         })