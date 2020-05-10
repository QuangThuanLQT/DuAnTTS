# -*- coding: utf-8 -*-
from odoo import http

# class TuanhuyPrintExcelQuotaion(http.Controller):
#     @http.route('/tuanhuy_print_excel_quotaion/tuanhuy_print_excel_quotaion/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tuanhuy_print_excel_quotaion/tuanhuy_print_excel_quotaion/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tuanhuy_print_excel_quotaion.listing', {
#             'root': '/tuanhuy_print_excel_quotaion/tuanhuy_print_excel_quotaion',
#             'objects': http.request.env['tuanhuy_print_excel_quotaion.tuanhuy_print_excel_quotaion'].search([]),
#         })

#     @http.route('/tuanhuy_print_excel_quotaion/tuanhuy_print_excel_quotaion/objects/<model("tuanhuy_print_excel_quotaion.tuanhuy_print_excel_quotaion"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tuanhuy_print_excel_quotaion.object', {
#             'object': obj
#         })