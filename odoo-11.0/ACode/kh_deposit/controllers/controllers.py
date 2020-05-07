# -*- coding: utf-8 -*-
from odoo import http

# class KhDeposit(http.Controller):
#     @http.route('/kh_deposit/kh_deposit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/kh_deposit/kh_deposit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('kh_deposit.listing', {
#             'root': '/kh_deposit/kh_deposit',
#             'objects': http.request.env['kh_deposit.kh_deposit'].search([]),
#         })

#     @http.route('/kh_deposit/kh_deposit/objects/<model("kh_deposit.kh_deposit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('kh_deposit.object', {
#             'object': obj
#         })