# -*- coding: utf-8 -*-
from odoo import http

# class PriniModifierAccessright(http.Controller):
#     @http.route('/prini_modifier_accessright/prini_modifier_accessright/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/prini_modifier_accessright/prini_modifier_accessright/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('prini_modifier_accessright.listing', {
#             'root': '/prini_modifier_accessright/prini_modifier_accessright',
#             'objects': http.request.env['prini_modifier_accessright.prini_modifier_accessright'].search([]),
#         })

#     @http.route('/prini_modifier_accessright/prini_modifier_accessright/objects/<model("prini_modifier_accessright.prini_modifier_accessright"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('prini_modifier_accessright.object', {
#             'object': obj
#         })