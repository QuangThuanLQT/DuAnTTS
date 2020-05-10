# -*- coding: utf-8 -*-
from odoo import http
from odoo import http, fields
from odoo.http import request
import json

# class TtsAccountKhoanThuKhac(http.Controller):
#     @http.route('/tts_account_khoan_thu_khac/tts_account_khoan_thu_khac/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tts_account_khoan_thu_khac/tts_account_khoan_thu_khac/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tts_account_khoan_thu_khac.listing', {
#             'root': '/tts_account_khoan_thu_khac/tts_account_khoan_thu_khac',
#             'objects': http.request.env['tts_account_khoan_thu_khac.tts_account_khoan_thu_khac'].search([]),
#         })

#     @http.route('/tts_account_khoan_thu_khac/tts_account_khoan_thu_khac/objects/<model("tts_account_khoan_thu_khac.tts_account_khoan_thu_khac"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tts_account_khoan_thu_khac.object', {
#             'object': obj
#         })
class Controller(http.Controller):
    @http.route('/export_overview_excel', type='http', auth='user')
    def report_detail(self, token, **post):
        sale_obj = request.env['sale.order']
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'Overview' + '.xlsx;')
            ]
        )
        domain = post.get('domain', False) and json.loads(post.get('domain', False))
        sale_obj.with_context(domain=domain).export_overview_excel(response)
        response.set_cookie('fileToken', token)
        return response