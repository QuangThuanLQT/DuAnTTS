# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class NkcReportController(http.Controller):

    @http.route('/print_nkc_excel', type='http', auth='user')
    def report_detail(self, token, **post):
        nkc = request.env['tts_journal_entry.nhatkychung']
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Nhat ky chung' + '.xlsx;')
            ]
        )
        nkc.print_nkc_excel(response)
        response.set_cookie('fileToken', token)
        return response
