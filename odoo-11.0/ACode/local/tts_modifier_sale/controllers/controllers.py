# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class ProductReportController(http.Controller):

    @http.route('/sale_export_data_over', type='http', auth='user')
    def report_over(self, token, **post):
        sale_obj = request.env['sale.order']
        action = post.get('action',False)
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        if action == 'sale.action_quotations':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Bao gia ban overview' + '.xlsx;')
                ]
            )
            sale_obj.with_context(domain=domain).print_quotaion_excel(response)
        elif action == 'sale.action_orders':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Export Overview' + '.xlsx;')
                ]
            )
            sale_obj.with_context(domain=domain).print_sale_excel(response)
        elif action == 'sale_purchase_returns.sale_order_return_action':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Export Overview' + '.xlsx;')
                ]
            )
            sale_obj.with_context(domain=domain).print_sale_excel(response, 'return')
        response.set_cookie('fileToken', token)
        return response

    @http.route('/sale_export_data_detail', type='http', auth='user')
    def report_detail(self, token, **post):
        sale_obj = request.env['sale.order']
        action = post.get('action', False)
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        if action == 'sale.action_quotations':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Bao gia ban detail' + '.xlsx;')
                ]
            )
            sale_obj.with_context(domain=domain).print_sale_excel_detail(response)
        elif action == 'sale.action_orders':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Export Detail' + '.xlsx;')
                ]
            )
            sale_obj.with_context(domain=domain).print_sale_excel_detail(response, 'sale')
        elif action == 'sale_purchase_returns.sale_order_return_action':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Export Detail' + '.xlsx;')
                ]
            )
            sale_obj.with_context(domain=domain).print_sale_excel_detail(response, 'return')
        response.set_cookie('fileToken', token)
        return response
