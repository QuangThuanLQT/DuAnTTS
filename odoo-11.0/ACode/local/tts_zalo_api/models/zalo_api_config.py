# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
import urllib


class zalo_api_config(models.Model):
    _name = 'zalo.api.config'

    name = fields.Char('Name')
    id_app = fields.Char('ID ứng dụng', required=False)
    secrect_key_app = fields.Char('Khóa bí mật của ứng dụng', required=False)
    oa_key = fields.Char(string='OA Secrect Key', required=False)
    access_token = fields.Char(string='Access Token', required=True)

    def convert_phone_number(self, phone_number):
        new = '84' + phone_number[1:]
        return new

    @api.model
    def _get_profile_url(self):
        return 'https://openapi.zalo.me/v2.0/oa/getprofile'

    @api.model
    def get_message_url(self):
        return 'https://openapi.zalo.me/v2.0/oa/message'

    def _getprofile(self, phone_number):
        headers = {"content-type": "application/x-www-form-urlencoded"}
        api_url_charge = self._get_profile_url()
        params = {
            'access_token': self.access_token,
            'data': "{'user_id': %s}" % self.convert_phone_number(phone_number)
        }
        r = requests.get(api_url_charge, params=params)
        result = r.json()
        return result

    def get_user_id(self, phone_number):
        user_id = False
        result = self._getprofile(phone_number)
        if result.get('data', False):
            if result.get('data').get('user_id'):
                user_id = result.get('data').get('user_id')
        return user_id

    def _send_message(self, user_id, message):
        headers = {"content-type": "application/json"}
        api_url_charge = self.get_message_url()
        params = {
            'access_token': self.access_token
        }
        body = {
            'recipient': {
                "user_id": user_id
            },
            'message': {
                "text": message
            }
        }
        r = requests.post(api_url_charge, params=params, json=body, headers=headers)
        result = r.json()
        return result
