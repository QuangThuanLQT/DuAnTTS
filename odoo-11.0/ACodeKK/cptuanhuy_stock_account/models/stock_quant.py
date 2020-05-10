# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    is_journal_later = fields.Boolean('Journal Later', default=False, compute='_compute_journal_later')

    @api.multi
    def _compute_journal_later(self):
        for quant in self:
            journal_later = False
            for move in quant.history_ids:
                if move.is_journal_later:
                    journal_later = True
                    break
            quant.is_journal_later = journal_later

    @api.model
    def create(self, values):
        record = super(StockQuant, self).create(values)
        return record

    @api.multi
    def write(self, values):
        result = super(StockQuant, self).write(values)
        return result


    def convert_to_local(self, utctime):
        timezone_tz = 'utc'
        if self.env.user and self.env.user.tz:
            timezone_tz = self.env.user.tz
        else:
            timezone_tz = 'Asia/Ho_Chi_Minh'
        local = pytz.timezone(timezone_tz)
        display_date_result = pytz.utc.localize(datetime.strptime(utctime,DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local)
        return str(display_date_result.date())

    def _create_account_move_line(self, move, credit_account_id, debit_account_id, journal_id):
        if move.picking_id and move.picking_id.min_date:
            datetime_to_date = self.convert_to_local(move.picking_id.min_date)
            self = self.with_context(force_set_date_by_picking=datetime_to_date)
        res = super(StockQuant, self)._create_account_move_line(move, credit_account_id, debit_account_id, journal_id)
        return res