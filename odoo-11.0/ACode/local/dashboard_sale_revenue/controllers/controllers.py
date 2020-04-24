# -*- coding: utf-8 -*-
from odoo import http

# class DashboardSaleRevenue(http.Controller):
#     @http.route('/dashboard_sale_revenue/dashboard_sale_revenue/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dashboard_sale_revenue/dashboard_sale_revenue/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dashboard_sale_revenue.listing', {
#             'root': '/dashboard_sale_revenue/dashboard_sale_revenue',
#             'objects': http.request.env['dashboard_sale_revenue.dashboard_sale_revenue'].search([]),
#         })

#     @http.route('/dashboard_sale_revenue/dashboard_sale_revenue/objects/<model("dashboard_sale_revenue.dashboard_sale_revenue"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dashboard_sale_revenue.object', {
#             'object': obj
#         })