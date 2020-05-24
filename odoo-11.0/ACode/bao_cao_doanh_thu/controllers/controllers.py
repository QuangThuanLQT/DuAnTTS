# -*- coding: utf-8 -*-
from odoo import http

# class BaoCaoDoanhThu(http.Controller):
#     @http.route('/bao_cao_doanh_thu/bao_cao_doanh_thu/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bao_cao_doanh_thu/bao_cao_doanh_thu/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bao_cao_doanh_thu.listing', {
#             'root': '/bao_cao_doanh_thu/bao_cao_doanh_thu',
#             'objects': http.request.env['bao_cao_doanh_thu.bao_cao_doanh_thu'].search([]),
#         })

#     @http.route('/bao_cao_doanh_thu/bao_cao_doanh_thu/objects/<model("bao_cao_doanh_thu.bao_cao_doanh_thu"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bao_cao_doanh_thu.object', {
#             'object': obj
#         })