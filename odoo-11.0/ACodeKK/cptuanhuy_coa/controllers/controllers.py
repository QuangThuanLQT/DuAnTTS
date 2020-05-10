# -*- coding: utf-8 -*-
from odoo import http

# class CptuanhuyCoa(http.Controller):
#     @http.route('/cptuanhuy_coa/cptuanhuy_coa/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cptuanhuy_coa/cptuanhuy_coa/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('cptuanhuy_coa.listing', {
#             'root': '/cptuanhuy_coa/cptuanhuy_coa',
#             'objects': http.request.env['cptuanhuy_coa.cptuanhuy_coa'].search([]),
#         })

#     @http.route('/cptuanhuy_coa/cptuanhuy_coa/objects/<model("cptuanhuy_coa.cptuanhuy_coa"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cptuanhuy_coa.object', {
#             'object': obj
#         })