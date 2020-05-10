# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


import json


class AccountReportController(http.Controller):
    @http.route('/print_account_report_excel', type='http', auth='user')
    def report(self, token, **post):
        aml = request.env['account.move.line']
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'account_report' + '.xlsx;')
            ]
        )
        aml.get_account_xlsx(post, response)
        response.set_cookie('fileToken', token)
        return response

    @http.route('/print_account_detail_excel', type='http', auth='user')
    def report_detail(self, token, **post):
        aml = request.env['account.move.line']
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'account_report' + '.xlsx;')
            ]
        )
        aml.get_account_detail_xlsx(post, response)
        response.set_cookie('fileToken', token)
        return response

    @http.route('/print_account_tong_hop_excel', type='http', auth='user')
    def report_tong_hop(self, token, **post):
        tong_hop_report = request.env['tong.hop.report']
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'account_report' + '.xlsx;')
            ]
        )
        account_code = post['code']
        account_id = request.env['account.account'].search([('code','=',account_code)]).id
        data = {'account_id': account_id, }
        if post['start_date']:
            start_date = datetime.strptime(post['start_date'],'%d/%m/%Y').strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            data.update({
                'start_date': start_date,
            })
        else:
            start_date = datetime.strptime('01/01/2017', '%d/%m/%Y').strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            data.update({
                'start_date': start_date,
            })
        if post['end_date']:
            end_date = datetime.strptime(post['end_date'],'%d/%m/%Y').strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            data.update({
                'end_date' : end_date,
            })
        tong_hop_report.create(data).print_excel(False,response)
        response.set_cookie('fileToken', token)
        return response


