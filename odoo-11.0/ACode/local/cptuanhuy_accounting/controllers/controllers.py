# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import json

class ProductReportController(http.Controller):
    @http.route('/account_asset_export_excel', type='http', auth='user')
    def report_over(self, token, **post):
        obj = request.env['account.asset.asset']
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Ke toan tai san' + '.xlsx;')
            ]
        )
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        obj.with_context(domain=domain).print_account_asset_excel(response)
        response.set_cookie('fileToken', token)
        return response
