# -*- coding: utf-8 -*-
from odoo import http

# class TuanhuyProject(http.Controller):
#     @http.route('/tuanhuy_project/tuanhuy_project/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tuanhuy_project/tuanhuy_project/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tuanhuy_project.listing', {
#             'root': '/tuanhuy_project/tuanhuy_project',
#             'objects': http.request.env['tuanhuy_project.tuanhuy_project'].search([]),
#         })

#     @http.route('/tuanhuy_project/tuanhuy_project/objects/<model("tuanhuy_project.tuanhuy_project"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tuanhuy_project.object', {
#             'object': obj
#         })