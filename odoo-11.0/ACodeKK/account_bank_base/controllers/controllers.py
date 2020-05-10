# -*- coding: utf-8 -*-
from odoo import http

# class AccountBankBase(http.Controller):
#     @http.route('/account_bank_base/account_bank_base/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_bank_base/account_bank_base/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_bank_base.listing', {
#             'root': '/account_bank_base/account_bank_base',
#             'objects': http.request.env['account_bank_base.account_bank_base'].search([]),
#         })

#     @http.route('/account_bank_base/account_bank_base/objects/<model("account_bank_base.account_bank_base"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_bank_base.object', {
#             'object': obj
#         })