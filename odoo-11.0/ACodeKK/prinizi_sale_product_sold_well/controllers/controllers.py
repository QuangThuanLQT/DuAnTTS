# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import json

class Controller(http.Controller):
    @http.route('/export_overview_sold_well', type='http', auth='user')
    def report_detail(self, token, **post):
        sale_obj = request.env['product.product']
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Overview' + '.xlsx;')
            ]
        )
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        sale_obj.with_context(domain=domain).export_overview_sold_well(response)
        response.set_cookie('fileToken', token)
        return response