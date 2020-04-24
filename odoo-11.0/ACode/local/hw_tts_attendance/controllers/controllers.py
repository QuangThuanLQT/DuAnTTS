# -*- coding: utf-8 -*-
from odoo import http
import odoo.addons.hw_proxy.controllers.main as hw_proxy

class HwTtsAttendance(hw_proxy.Proxy):

    @http.route('/hw_proxy/tts_attendance', type='json', auth='none', cors='*')
    def tts_attendance(self):
        return '1234'
