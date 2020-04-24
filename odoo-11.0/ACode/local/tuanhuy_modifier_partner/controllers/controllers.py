# -*- coding: utf-8 -*-
from odoo import http

# class TuanhuyModifierPartner(http.Controller):
#     @http.route('/tuanhuy_modifier_partner/tuanhuy_modifier_partner/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tuanhuy_modifier_partner/tuanhuy_modifier_partner/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tuanhuy_modifier_partner.listing', {
#             'root': '/tuanhuy_modifier_partner/tuanhuy_modifier_partner',
#             'objects': http.request.env['tuanhuy_modifier_partner.tuanhuy_modifier_partner'].search([]),
#         })

#     @http.route('/tuanhuy_modifier_partner/tuanhuy_modifier_partner/objects/<model("tuanhuy_modifier_partner.tuanhuy_modifier_partner"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tuanhuy_modifier_partner.object', {
#             'object': obj
#         })