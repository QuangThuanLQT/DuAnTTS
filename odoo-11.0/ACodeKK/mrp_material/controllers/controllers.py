# -*- coding: utf-8 -*-
from odoo import http

# class MrpMaterial(http.Controller):
#     @http.route('/mrp_material/mrp_material/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mrp_material/mrp_material/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mrp_material.listing', {
#             'root': '/mrp_material/mrp_material',
#             'objects': http.request.env['mrp_material.mrp_material'].search([]),
#         })

#     @http.route('/mrp_material/mrp_material/objects/<model("mrp_material.mrp_material"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mrp_material.object', {
#             'object': obj
#         })