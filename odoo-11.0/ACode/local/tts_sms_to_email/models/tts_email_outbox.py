# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import re


class tts_sms_outbox(models.Model):
    _name = 'tts.sms.outbox'
    _inherit = ['mail.thread', 'ir.needaction_mixin', 'utm.mixin', 'rating.mixin']

    name = fields.Char()
    phone = fields.Char()
    body = fields.Text(store=True)
    date = fields.Datetime('Date')

    @api.model
    def message_new(self, msg, custom_values=None):
        values = dict(custom_values or {}, name=msg.get('subject'))
        format = re.compile('<.*?>')
        message = re.sub(format, '', msg.get('body', False))
        data = message.split(',')
        if len(data) >= 3:
            phone = data[1].strip()
            body = data[2].strip()
            values.update({
                'phone': phone,
                'body': body
            })
        return super(tts_sms_outbox, self).message_new(msg, custom_values=values)
