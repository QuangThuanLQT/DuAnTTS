# -*- coding: utf-8 -*-
from odoo import http

# class TuanhuyTranslation2(http.Controller):
#     @http.route('/tuanhuy_translation2/tuanhuy_translation2/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tuanhuy_translation2/tuanhuy_translation2/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tuanhuy_translation2.listing', {
#             'root': '/tuanhuy_translation2/tuanhuy_translation2',
#             'objects': http.request.env['tuanhuy_translation2.tuanhuy_translation2'].search([]),
#         })

#     @http.route('/tuanhuy_translation2/tuanhuy_translation2/objects/<model("tuanhuy_translation2.tuanhuy_translation2"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tuanhuy_translation2.object', {
#             'object': obj
#         })