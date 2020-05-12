# -*- coding: utf-8 -*-
from odoo import http

# class AFeoscoBase(http.Controller):
#     @http.route('/a_feosco_base/a_feosco_base/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/a_feosco_base/a_feosco_base/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('a_feosco_base.listing', {
#             'root': '/a_feosco_base/a_feosco_base',
#             'objects': http.request.env['a_feosco_base.a_feosco_base'].search([]),
#         })

#     @http.route('/a_feosco_base/a_feosco_base/objects/<model("a_feosco_base.a_feosco_base"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('a_feosco_base.object', {
#             'object': obj
#         })