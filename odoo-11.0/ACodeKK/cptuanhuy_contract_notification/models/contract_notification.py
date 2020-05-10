# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta

class contract_notification_settings(models.Model):
    _name = 'contract.notification.settings'

    name = fields.Char('Tên')
    parnter_ids = fields.Many2many('res.partner', string="Người nhận", required=1)
    day_number = fields.Integer(string='Số ngày', default=1, required=1)
    email_template = fields.Many2one('mail.template', string='Mẫu Email', required=1,
                                     domain=[('model_id.model', '=', 'contract.notification.settings')])


    @api.multi
    def send_email_contract_notification(self):
        now = datetime.today().date()
        today_str = datetime.strftime(datetime.today().date(), DEFAULT_SERVER_DATE_FORMAT)
        for record in self.search([]):
            list_contract = []
            daynumber = record.day_number
            for contract in self.env['account.analytic.account'].search([('date_end', '!=', False)]):
                date_end = datetime.strptime(contract.date_end, DEFAULT_SERVER_DATETIME_FORMAT).date() - relativedelta(days=daynumber)
                if date_end == now:
                    list_contract.append(contract)
            list_email = []
            for partner_id in record.parnter_ids:
                email = partner_id.email or partner_id.user_ids and partner_id.user_ids.email
                if email:
                    list_email.append(email)
            email_to = ', '.join(list_email)
            email_template = record.email_template
            email_template.email_to = email_to
            email_template.with_context(data=list_contract).send_mail(record.id, force_send=True, raise_exception=True)
