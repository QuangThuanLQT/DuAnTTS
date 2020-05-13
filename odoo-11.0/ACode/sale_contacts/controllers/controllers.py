# -*- coding: utf-8 -*-
from odoo import http

# class SaleContacts(http.Controller):
#     @http.route('/sale_contacts/sale_contacts/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_contacts/sale_contacts/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_contacts.listing', {
#             'root': '/sale_contacts/sale_contacts',
#             'objects': http.request.env['sale_contacts.sale_contacts'].search([]),
#         })

#     @http.route('/sale_contacts/sale_contacts/objects/<model("sale_contacts.sale_contacts"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_contacts.object', {
#             'object': obj
#         })