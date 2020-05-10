# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class zalo_api_test(models.Model):
    _name = 'zalo.api.test'

    phone = fields.Char('SDT', required=True)
    mess = fields.Text('Nội dung', required=True)

    def send_message(self):
        zalo_api = self.env.ref('tts_zalo_api.zalo_api_config')
        user_id = zalo_api.get_user_id(self.phone)
        if user_id:
            result = zalo_api._send_message(user_id, self.mess)
            if result.get('error', False) == 0:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Warning : Success',
                    'res_model': 'zalo.api.test',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': self.env.ref('tts_zalo_api.zalo_api_test_wizard_success', False).id,
                    'target': 'new',
                }
            else:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Warning : Fail',
                    'res_model': 'zalo.api.test',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': self.env.ref('tts_zalo_api.zalo_api_test_wizard_fail', False).id,
                    'target': 'new',
                }
        else:
            raise UserError(_("SDT không đúng."))
