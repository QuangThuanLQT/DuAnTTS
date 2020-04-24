# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import json
from datetime import date


class PartnerController(http.Controller):
    @http.route('/print_sms_inbox_detail', type='http', auth='user')
    def sms_inbox_detail(self, token, **post):
        sms_obj = request.env['tts.sms.inbox']
        action = post.get('action', False)

        domain = post.get('domain', False) and json.loads(post.get('domain', False))

        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', 'attachment; filename=' + 'SMS_Detail' + '.xlsx;')
            ]
        )
        sms_obj.with_context(domain=domain).print_sms_detail(response)
        response.set_cookie('fileToken', token)
        return response
