# -*- coding: utf-8 -*-
from odoo import http

# class ModifierMergeProduct(http.Controller):
#     @http.route('/modifier_merge_product/modifier_merge_product/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/modifier_merge_product/modifier_merge_product/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('modifier_merge_product.listing', {
#             'root': '/modifier_merge_product/modifier_merge_product',
#             'objects': http.request.env['modifier_merge_product.modifier_merge_product'].search([]),
#         })

#     @http.route('/modifier_merge_product/modifier_merge_product/objects/<model("modifier_merge_product.modifier_merge_product"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('modifier_merge_product.object', {
#             'object': obj
#         })