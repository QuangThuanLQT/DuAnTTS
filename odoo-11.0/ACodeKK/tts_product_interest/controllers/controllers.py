# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class TtsProductInterest(http.Controller):
    @http.route('/print_product_interest_excel', type='http', auth='user')
    def report_detail(self, token, **post):
        product_interest_obj = request.env['product.interest']

        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Product Interested' + '.xlsx;')
            ]
        )
        product_interest_obj.with_context(domain=domain).print_product_interest_excel(response)

        response.set_cookie('fileToken', token)
        return response