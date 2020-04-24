# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import json


class PartnerController(http.Controller):
    @http.route('/print_partner_excel', type='http', auth='user')
    def report_detail(self, token, **post):
        sale_obj = request.env['res.partner']
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Customers' + '.xlsx;')
            ]
        )
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        sale_obj.with_context(domain=domain).print_partner_excel(response)
        response.set_cookie('fileToken', token)
        return response
