# -*- coding: utf-8 -*-
from odoo import http

# class TuanhuyInvoice(http.Controller):
#     @http.route('/tuanhuy_invoice/tuanhuy_invoice/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tuanhuy_invoice/tuanhuy_invoice/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tuanhuy_invoice.listing', {
#             'root': '/tuanhuy_invoice/tuanhuy_invoice',
#             'objects': http.request.env['tuanhuy_invoice.tuanhuy_invoice'].search([]),
#         })

#     @http.route('/tuanhuy_invoice/tuanhuy_invoice/objects/<model("tuanhuy_invoice.tuanhuy_invoice"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tuanhuy_invoice.object', {
#             'object': obj
#         })