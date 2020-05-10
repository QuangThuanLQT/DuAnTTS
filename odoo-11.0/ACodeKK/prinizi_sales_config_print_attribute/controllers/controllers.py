# -*- coding: utf-8 -*-
from odoo import http

# class PriniziSalesConfigPrintAttribute(http.Controller):
#     @http.route('/prinizi_sales_config_print_attribute/prinizi_sales_config_print_attribute/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/prinizi_sales_config_print_attribute/prinizi_sales_config_print_attribute/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('prinizi_sales_config_print_attribute.listing', {
#             'root': '/prinizi_sales_config_print_attribute/prinizi_sales_config_print_attribute',
#             'objects': http.request.env['prinizi_sales_config_print_attribute.prinizi_sales_config_print_attribute'].search([]),
#         })

#     @http.route('/prinizi_sales_config_print_attribute/prinizi_sales_config_print_attribute/objects/<model("prinizi_sales_config_print_attribute.prinizi_sales_config_print_attribute"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('prinizi_sales_config_print_attribute.object', {
#             'object': obj
#         })