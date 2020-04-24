# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import urllib


class tts_api(models.Model):
    _name = 'esms.api.config'

    api_key = fields.Char('API Key', required=1)
    secret_key = fields.Char('Secret Key', required=1)
    brand_name = fields.Char('Brand name', required=True)
    sms_type = fields.Char('SMS Type', required=True)

    @api.model
    def _get_sms_api_url(self):
        return 'rest.esms.vn/MainService.svc/json'

    def _create_sms_partner(self, params):
        headers = {"content-type": "application/x-www-form-urlencoded"}
        api_url_charge = 'http://%s/SendMultipleMessage_V4_get' % (self._get_sms_api_url())
        params.update({
            'ApiKey': self.api_key,
            'SecretKey': self.secret_key,
            'SmsType': self.sms_type,
            'Brandname': self.brand_name,
        })
        r = requests.get(api_url_charge, params=params, headers=headers)
        result = r.json()
        # if result.get('CodeResult', False) != '100':
        #     return {
        #         'warning': {
        #             'title': _('Warning'),
        #             'message': _('Gởi tin nhắn thất bại.')
        #         }
        #     }
        return result
