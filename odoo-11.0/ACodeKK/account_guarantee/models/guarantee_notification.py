# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta


class guarantee_notification_settings(models.Model):
    _name = 'guarantee.notification.settings'

    name = fields.Char('Tên')
    parnter_ids = fields.Many2many('res.partner', string="Người nhận", required=1)
    day_number = fields.Integer(string='Số ngày', default=1, required=1)
    email_template = fields.Many2one('mail.template', string='Mẫu Email', required=1, domain=[('model_id.model', '=', 'guarantee.notification.settings')])

    @api.multi
    def send_email_guarantee_notification(self):
        now = datetime.today().date()
        today_str = datetime.strftime(datetime.today().date(), DEFAULT_SERVER_DATE_FORMAT)
        for record in self.search([]):
            list_guarantee = []
            daynumber = record.day_number
            for guarantee in self.env['account.guarantee'].search([('end_date', '!=', False)]):
                end_date = datetime.strptime(guarantee.end_date, DEFAULT_SERVER_DATE_FORMAT).date() - relativedelta(
                    days=daynumber)
                if end_date == now:
                    list_guarantee.append(guarantee)
            list_email = []
            for partner_id in record.parnter_ids:
                email = partner_id.email or partner_id.user_ids and partner_id.user_ids.email
                if email:
                    list_email.append(email)
            email_to = ', '.join(list_email)
            email_template = record.email_template
            email_template.email_to = email_to
            email_template.with_context(data=list_guarantee).send_mail(record.id, force_send=True, raise_exception=True)
