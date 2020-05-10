# -*- coding: utf-8 -*-
from odoo import models, fields, api
# from datetime import datetime
from dateutil.relativedelta import relativedelta
import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import pytz

class tuanhuy_lock_poup(models.TransientModel):
    _name = 'lock.sale.puchase.popup'

    date_start  = fields.Date('Thời gian bắt đầu',required=True)
    date_end    = fields.Date('Thời gian kết thúc',required=True)

    @api.multi
    def confirm_lock(self):
        if self.date_start and self.date_end:
            date_start = self.convert_to_utc(self.date_start)
            date_end = self.convert_to_utc((datetime.datetime.strptime(self.date_end,DEFAULT_SERVER_DATE_FORMAT) + relativedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT))
            self.env.cr.execute("UPDATE sale_order SET state = 'done' where state = 'sale' and date_order >= '%s' and date_order <= '%s'" % (date_start, date_end))
            self.env.cr.execute("UPDATE purchase_order SET state = 'done' where state = 'purchase' and date_order >= '%s' and date_order <= '%s'" % (date_start, date_end))
            # sale_ids = self.env['sale.order'].sudo().search([('date_order','>=',date_start),('date_order','<=',date_end),('state','=','sale')])
            # if sale_ids:
            #     sale_ids.action_done()
            # purchase_ids = self.env['purchase.order'].sudo().search([('date_order', '>=', date_start), ('date_order', '<=', date_end), ('state', '=', 'purchase')])
            # if purchase_ids:
            #     purchase_ids.button_done()

    def convert_to_utc(self, date):
        timezone_tz = 'Asia/Ho_Chi_Minh'
        if self.env.user and self.env.user.tz:
            timezone_tz = self.env.user.tz
        else:
            timezone_tz = 'Asia/Ho_Chi_Minh'
        date_from = datetime.datetime.strptime(date,DEFAULT_SERVER_DATE_FORMAT).replace(tzinfo=pytz.timezone(timezone_tz)).astimezone(pytz.utc)
        return date_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)