# -*- coding: utf-8 -*-
from odoo import http

# class EmployeesQt(http.Controller):
#     @http.route('/employees__qt/employees__qt/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/employees__qt/employees__qt/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('employees__qt.listing', {
#             'root': '/employees__qt/employees__qt',
#             'objects': http.request.env['employees__qt.employees__qt'].search([]),
#         })

#     @http.route('/employees__qt/employees__qt/objects/<model("employees__qt.employees__qt"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('employees__qt.object', {
#             'object': obj
#         })