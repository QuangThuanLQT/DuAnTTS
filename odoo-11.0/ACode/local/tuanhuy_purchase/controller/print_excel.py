# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class AccountReportController(http.Controller):
    @http.route('/print_purchase_order_line', type='http', auth='user')
    def report(self, token, **post):
        pol = request.env['purchase.order.line']
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'San Pham Da Mua' + '.xlsx;')
            ]
        )
        pol.print_excel_report(post, response)
        response.set_cookie('fileToken', token)
        return response