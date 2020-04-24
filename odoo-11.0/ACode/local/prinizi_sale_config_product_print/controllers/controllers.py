# -*- coding: utf-8 -*-
from odoo import http

# class PriniziSaleConfigProductPrint(http.Controller):
#     @http.route('/prinizi_sale_config_product_print/prinizi_sale_config_product_print/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/prinizi_sale_config_product_print/prinizi_sale_config_product_print/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('prinizi_sale_config_product_print.listing', {
#             'root': '/prinizi_sale_config_product_print/prinizi_sale_config_product_print',
#             'objects': http.request.env['prinizi_sale_config_product_print.prinizi_sale_config_product_print'].search([]),
#         })

#     @http.route('/prinizi_sale_config_product_print/prinizi_sale_config_product_print/objects/<model("prinizi_sale_config_product_print.prinizi_sale_config_product_print"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('prinizi_sale_config_product_print.object', {
#             'object': obj
#         })