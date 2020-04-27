# -*- coding: utf-8 -*-
from odoo import http

# class HangHoa(http.Controller):
#     @http.route('/hang_hoa/hang_hoa/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hang_hoa/hang_hoa/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hang_hoa.listing', {
#             'root': '/hang_hoa/hang_hoa',
#             'objects': http.request.env['hang_hoa.hang_hoa'].search([]),
#         })

#     @http.route('/hang_hoa/hang_hoa/objects/<model("hang_hoa.hang_hoa"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hang_hoa.object', {
#             'object': obj
#         })