# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import json
from datetime import date


class PartnerController(http.Controller):
    @http.route('/print_partner_excel', type='http', auth='user')
    def report_detail(self, token, **post):
        sale_obj = request.env['res.partner']
        action = post.get('action', False)

        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        if action in ['base.action_partner_form','base.action_partner_customer_form']:
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Customers' + '.xlsx;')
                ]
            )
            sale_obj.with_context(domain=domain).print_partner_excel(response)
        elif action == 'base.action_partner_supplier_form':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Vendors' + '.xlsx;')
                ]
            )
            sale_obj.with_context(domain=domain).print_vendors_excel(response)
        # sale_obj.with_context(domain=domain).print_partner_excel(response)
        response.set_cookie('fileToken', token)
        return response

    @http.route('/print_detail_partner_excel', type='http', auth='user')
    def report_detail_partner(self, token, **post):
        sale_obj = request.env['res.partner']
        action = post.get('action', False)

        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        if action in ['base.action_partner_form', 'base.action_partner_customer_form']:
            today = date.today()
            d1 = today.strftime("%d%m%Y")
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Customer Details - ' + d1 + '.xlsx')
                ]
            )
            sale_obj.with_context(domain=domain).print_partner_detail_excel(response)
        elif action == 'base.action_partner_supplier_form':
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=' + 'Vendors' + '.xlsx;')
                ]
            )
            sale_obj.with_context(domain=domain).print_vendors_detail_excel(response)
        # sale_obj.with_context(domain=domain).print_partner_excel(response)
        response.set_cookie('fileToken', token)
        return response
