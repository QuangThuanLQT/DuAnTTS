# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import calendar
import json
import StringIO
import xlsxwriter
from odoo.tools import config

import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class ReportAccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"

    def get_debit_ck_from_thcn(self,list_account,start_date,end_date):
        cno_obj = self.env['tong.hop.cong.no.report'].search([])
        account_id = self.env['account.account'].search([('code','in',list_account)])
        if account_id :
            return sum(cno_obj.with_context(account_id=account_id.ids,congno_date_from=start_date,congno_date_to=end_date).mapped('after_debit'))
        else:
            return 0

    def get_debit_dk_from_thcn(self,list_account,start_date,end_date):
        cno_obj = self.env['tong.hop.cong.no.report'].search([])
        account_id = self.env['account.account'].search([('code','in',list_account)])
        if account_id :
            return sum(cno_obj.with_context(account_id=account_id.ids,congno_date_from=start_date,congno_date_to=end_date).mapped('before_debit'))
        else:
            return 0

    def get_credit_ck_from_thcn(self,list_account,start_date,end_date):
        cno_obj = self.env['tong.hop.cong.no.report'].search([])
        account_id = self.env['account.account'].search([('code','in',list_account)])
        if account_id :
            return sum(cno_obj.with_context(account_id=account_id.ids,congno_date_from=start_date,congno_date_to=end_date).mapped('after_credit'))
        else:
            return 0

    def get_credit_dk_from_thcn(self,list_account,start_date,end_date):
        cno_obj = self.env['tong.hop.cong.no.report'].search([])
        account_id = self.env['account.account'].search([('code','in',list_account)])
        if account_id:
            return sum(cno_obj.with_context(account_id=account_id.ids,congno_date_from=start_date,congno_date_to=end_date).mapped('before_credit'))
        else:
            return 0

    @api.multi
    def get_lines(self, context_id, line_id=None):
        res = super(ReportAccountFinancialReport, self).get_lines(context_id, line_id)
        ref = self.env.ref('tuanhuy_account_reports.tuanhuy_hoatdong_kinhdoanh_report')
        luuhcuyentiente = self.env.ref('tuanhuy_account_reports.tuanhuy_financial_report_cashsummary0')
        bangcandoi = self.env.ref('tuanhuy_account_reports.account_financial_report_balancesheet0')
        start_date = context_id.date_from
        end_date = context_id.date_to
        if context_id.date_filter == 'custom':
            if not context_id.date_from:
                if context_id.date_to:
                    start_date = datetime.strptime(context_id.date_to, '%Y-%m-%d') - relativedelta(months=1)
                    start_date = start_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                else:
                    start_date = fields.Date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
            # temp    = relativedelta(datetime.strptime(end_date, "%Y-%m-%d"), start_date)
            # month   = temp.months + 1 if temp.years < 1 else temp.months + 1 + temp.years * 12
            end_l   = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)
            start_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(months=1)
        elif context_id.date_filter == 'this_month':
            start_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(months=1)
            end_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)
        elif context_id.date_filter == 'this_year':
            start_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(years=1)
            end_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)
        elif context_id.date_filter == 'last_month':
            start_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(months=1)
            end_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)
        elif context_id.date_filter == 'last_quarter':
            start_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(months=3)
            end_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)
        elif context_id.date_filter == 'last_year':
            start_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(years=1)
            end_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)
        else:
            start_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(years=1)
            end_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)
        start_date_l = start_l.strftime(DEFAULT_SERVER_DATE_FORMAT)
        end_date_l = end_l.strftime(DEFAULT_SERVER_DATE_FORMAT)
        if self.id == ref.id:
            for line in res:
                if 'id' in line and line['id']:
                    record = self.env['account.financial.html.report.line'].browse(line['id'])
                    line.update({'code':record.code or False})
                    if context_id.date_filter == 'custom':
                        # line.update({'date_filter': 'custom' or False,'date_from':context_id.date_from or False,'date_to':context_id.date_to or False })
                        domain = []
                        if context_id.date_from:
                            domain.append(('date','>=',context_id.date_from))
                        if context_id.date_to:
                            domain.append(('date','<=',context_id.date_to))
                        if domain:
                            line.update({'domain':domain})
                    if record.number == '01':
                        journal_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '511' + '%'),
                            ('date', '>=', start_date),
                            ('date', '<=', end_date)
                        ])
                        journal_items_l = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '511'),
                            ('date', '>=', start_date_l),
                            ('date', '<=', end_date_l)
                        ])

                        record.current_year = sum(journal_items.mapped('credit')) if journal_items else 0
                        record.last_year = sum(journal_items_l.mapped('credit')) if journal_items_l else 0
                    elif record.number == '02':
                        # journal_items_credit = self.env['account.move.line'].search([
                        #     # '|', '|', '|', '|', '|',
                        #     ('account_id.code', 'ilike', '521'),
                        #      # ('account_id.code', 'ilike', '532'),
                        #      # ('account_id.code', 'ilike', '531'),
                        #      # ('account_id.code', '=', '3332'),
                        #      # ('account_id.code', '=', '3333'),
                        #      # ('account_id.code', '=', '3331'),
                        #     ('date', '>=', start_date),
                        #     ('date', '<=', end_date)
                        # ])
                        journal_items = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '521'),
                            ('date', '>=', start_date),
                            ('date', '<=', end_date)
                        ])

                        journal_items_l = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '521'),
                            ('date', '>=', start_date_l),
                            ('date', '<=', end_date_l)
                        ])

                        record.current_year = sum(journal_items.mapped('debit')) if journal_items else 0
                        record.last_year = sum(journal_items_l.mapped('debit')) if journal_items_l else 0

                    elif record.number == '10':
                        record.current_year = self.get_in_finanial_line(res, '01').current_year - self.get_in_finanial_line(res, '02').current_year
                        record.last_year = self.get_in_finanial_line(res, '01').last_year - self.get_in_finanial_line(res, '02').last_year

                    elif record.number == '11':
                        journal_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '632%'),
                            ('date', '>=', start_date),
                            ('date', '<=', end_date)
                        ])

                        journal_items_l = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '632%'),
                            ('date', '>=', start_date_l),
                            ('date', '<=', end_date_l)
                        ])

                        record.current_year = (sum(journal_items.mapped('debit')) if journal_items else 0) - (sum(journal_items.mapped('credit')) if journal_items else 0)
                        record.last_year = (sum(journal_items_l.mapped('debit')) if journal_items_l else 0) - (sum(journal_items_l.mapped('credit')) if journal_items_l else 0)

                    elif record.number == '20':
                        record.current_year = self.get_in_finanial_line(res,
                                                                        '10').current_year - self.get_in_finanial_line(
                            res, '11').current_year
                        record.last_year = self.get_in_finanial_line(res, '10').last_year - self.get_in_finanial_line(res,
                                                                                                                    '11').last_year

                    elif record.number == '21':
                        journal_items = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '515'),
                            ('date', '>=', start_date),
                            ('date', '<=', end_date)
                        ])

                        journal_items_l = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '515'),
                            ('date', '>=', start_date_l),
                            ('date', '<=', end_date_l)
                        ])

                        record.current_year = (sum(journal_items.mapped('credit')) if journal_items else 0) - \
                                              (sum(journal_items.mapped('debit')) if journal_items else 0)
                        record.last_year = (sum(journal_items_l.mapped('credit')) if journal_items_l else 0) - \
                                           (sum(journal_items_l.mapped('debit')) if journal_items_l else 0)

                    elif record.number == '22':
                        journal_items = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '635'),
                            ('date', '>=', start_date),
                            ('date', '<=', end_date)
                        ])

                        journal_items_l = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '635'),
                            ('date', '>=', start_date_l),
                            ('date', '<=', end_date_l)
                        ])

                        record.current_year = (sum(journal_items.mapped('debit')) if journal_items else 0) - \
                                              (sum(journal_items.mapped('credit')) if journal_items else 0)
                        record.last_year = (sum(journal_items_l.mapped('debit')) if journal_items_l else 0) - \
                                           (sum(journal_items_l.mapped('credit')) if journal_items_l else 0)

                    elif record.number == '23':
                        journal_items = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '635'),
                            ('date', '>=', start_date),
                            ('date', '<=', end_date)
                        ])

                        journal_items_l = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '635'),
                            ('date', '>=', start_date_l),
                            ('date', '<=', end_date_l)
                        ])

                        record.current_year = (sum(journal_items.mapped('debit')) if journal_items else 0) - \
                                              (sum(journal_items.mapped('credit')) if journal_items else 0)
                        record.last_year = (sum(journal_items_l.mapped('debit')) if journal_items_l else 0) - \
                                           (sum(journal_items_l.mapped('credit')) if journal_items_l else 0)
                    elif record.number == '24':
                        journal_items = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '642'),
                            ('date', '>=', start_date),
                            ('date', '<=', end_date)
                        ])

                        journal_items_l = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '642'),
                            ('date', '>=', start_date_l),
                            ('date', '<=', end_date_l)
                        ])

                        record.current_year = (sum(journal_items.mapped('debit')) if journal_items else 0) - \
                                              (sum(journal_items.mapped('credit')) if journal_items else 0)
                        record.last_year = (sum(journal_items_l.mapped('debit')) if journal_items_l else 0) - \
                                           (sum(journal_items_l.mapped('credit')) if journal_items_l else 0)

                    elif record.number == '25':
                        journal_items = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '641'),
                            ('date', '>=', start_date),
                            ('date', '<=', end_date)
                        ])

                        journal_items_l = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '641'),
                            ('date', '>=', start_date_l),
                            ('date', '<=', end_date_l)
                        ])

                        record.current_year = (sum(journal_items.mapped('debit')) if journal_items else 0) - \
                                              (sum(journal_items.mapped('credit')) if journal_items else 0)
                        record.last_year = (sum(journal_items_l.mapped('debit')) if journal_items_l else 0) - \
                                           (sum(journal_items_l.mapped('credit')) if journal_items_l else 0)

                    elif record.number == '26':
                        journal_items = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '642'),
                            ('date', '>=', start_date),
                            ('date', '<=', end_date)
                        ])

                        journal_items_l = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '642'),
                            ('date', '>=', start_date_l),
                            ('date', '<=', end_date_l)
                        ])

                        record.current_year = (sum(journal_items.mapped('debit')) if journal_items else 0) - \
                                              (sum(journal_items.mapped('credit')) if journal_items else 0)
                        record.last_year = (sum(journal_items_l.mapped('debit')) if journal_items_l else 0) - \
                                           (sum(journal_items_l.mapped('credit')) if journal_items_l else 0)

                    elif record.number == '30':
                        record.current_year = self.get_in_finanial_line(res, '20').current_year + (
                        self.get_in_finanial_line(res, '21').current_year - self.get_in_finanial_line(res,
                                                                                                    '22').current_year) - (
                                              self.get_in_finanial_line(res,
                                                                        '25').current_year + self.get_in_finanial_line(
                                                  res, '26').current_year)
                        record.last_year = self.get_in_finanial_line(res, '20').last_year + (
                        self.get_in_finanial_line(res, '21').last_year - self.get_in_finanial_line(res,
                                                                                                    '22').last_year) - (
                                              self.get_in_finanial_line(res,
                                                                        '25').last_year + self.get_in_finanial_line(
                                                  res, '26').last_year)

                    elif record.number == '31':
                        journal_items = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '711'),
                            ('date', '>=', start_date),
                            ('date', '<=', end_date)
                        ])

                        journal_items_l = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '711'),
                            ('date', '>=', start_date_l),
                            ('date', '<=', end_date_l)
                        ])

                        record.current_year = (sum(journal_items.mapped('credit')) if journal_items else 0) - \
                                              (sum(journal_items.mapped('debit')) if journal_items else 0)
                        record.last_year = (sum(journal_items_l.mapped('credit')) if journal_items_l else 0) - \
                                           (sum(journal_items_l.mapped('debit')) if journal_items_l else 0)

                    elif record.number == '32':
                        journal_items = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '811%'),
                            ('date', '>=', start_date),
                             ('date', '<=', end_date)
                        ])

                        journal_items_l = self.env['account.move.line'].search([
                            ('account_id.code', '=like', '811%'),
                            ('date', '>=', start_date_l),
                            ('date', '<=', end_date_l)
                        ])

                        record.current_year = (sum(journal_items.mapped('debit')) if journal_items else 0) - \
                                              (sum(journal_items.mapped('credit')) if journal_items else 0)
                        record.last_year = (sum(journal_items_l.mapped('debit')) if journal_items_l else 0) - \
                                           (sum(journal_items_l.mapped('credit')) if journal_items_l else 0)

                    elif record.number == '40':
                        record.current_year = self.get_in_finanial_line(res, '31').current_year - self.get_in_finanial_line(res, '32').current_year
                        record.last_year = self.get_in_finanial_line(res, '31').last_year - self.get_in_finanial_line(res, '32').last_year

                    elif record.number == '50':
                        record.current_year = self.get_in_finanial_line(res, '30').current_year + self.get_in_finanial_line(res, '40').current_year
                        record.last_year = self.get_in_finanial_line(res, '30').last_year + self.get_in_finanial_line(res, '40').last_year

                    elif record.number == '51':
                        journal_items = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '8211'),
                            ('date', '>=', start_date),
                            ('date', '<=', end_date)
                        ])

                        journal_items_l = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '8211'),
                            ('date', '>=', start_date_l),
                            ('date', '<=', end_date_l)
                        ])

                        record.current_year = (sum(journal_items.mapped('credit')) if journal_items else 0) - \
                                              (sum(journal_items.mapped('debit')) if journal_items else 0)
                        record.last_year = (sum(journal_items_l.mapped('credit')) if journal_items_l else 0) - \
                                           (sum(journal_items_l.mapped('debit')) if journal_items_l else 0)
                    elif record.number == '52':
                        journal_items = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '8212'),
                            ('date', '>=', start_date),
                            ('date', '<=', end_date)
                        ])

                        journal_items_l = self.env['account.move.line'].search([
                            ('account_id.code', 'ilike', '8212'),
                            ('date', '>=', start_date_l),
                            ('date', '<=', end_date_l)
                        ])

                        record.current_year = (sum(journal_items.mapped('credit')) if journal_items else 0) - \
                                              (sum(journal_items.mapped('debit')) if journal_items else 0)
                        record.last_year = (sum(journal_items_l.mapped('credit')) if journal_items_l else 0) - \
                                           (sum(journal_items_l.mapped('debit')) if journal_items_l else 0)

                    elif record.number == '60':
                        record.current_year = self.get_in_finanial_line(res, '50').current_year - self.get_in_finanial_line(res, '51').current_year
                        record.last_year = self.get_in_finanial_line(res, '50').last_year - self.get_in_finanial_line(res, '51').last_year
                    number = record.number if record.number else ""
                    if record.number == '60':
                        result_now = (record.current_year / self.get_in_finanial_line(res, '10').current_year) * 100 if record.current_year and self.get_in_finanial_line(res, '10').current_year else 0
                        result_last = (record.last_year / self.get_in_finanial_line(res, '10').last_year) * 100 if record.last_year and self.get_in_finanial_line(res, '10').last_year else 0
                        line['report'] = [number, "", ('{0:,.1f}'.format(record.current_year) if record.current_year >= 0 else '({0:,.1f})'.format(abs(record.current_year))) if number else "",
                                          ('{0:,.1f}'.format(record.last_year) if record.last_year >= 0 else '({0:,.1f})'.format(abs(record.last_year))) if number else ""]
                    else:
                        line['report'] = [number, "", ('{0:,.1f}'.format(record.current_year) if record.current_year >= 0 else '({0:,.1f})'.format(abs(record.current_year))) if number else "",
                                          ('{0:,.1f}'.format(record.last_year) if record.last_year >= 0 else '({0:,.1f})'.format(abs(record.last_year))) if number else ""]
        elif self.id == luuhcuyentiente.id:
            for line in (filter(lambda x: x['level'] == 2, res)):
                if 'id' in line and line['id']:
                    record = self.env['account.financial.html.report.line'].browse(line['id'])
                    number = record.number if record.number else ""
                    if number == '01':
                        list_account_credit = ['511', '131', '121', '515']
                        list_account_debit = ['111', '112']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                 list_account_credit, start_date,
                                                                                 end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)
                    if number == '02':
                        list_account_credit = ['111', '112']
                        list_account_debit = ['331', '151', '152', '153', '156']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                 list_account_credit, start_date,
                                                                                 end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)
                    if number == '03':
                        list_account_debit = ['334']
                        list_account_credit = ['111', '112']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                 list_account_credit, start_date,
                                                                                 end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)
                    if number == '04':
                        list_account_debit = ['242', '335', '635']
                        list_account_credit = ['111', '112', '113']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                 list_account_credit, start_date,
                                                                                 end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)
                    if number == '05':
                        list_account_debit = ['3334']
                        list_account_credit = ['111', '112', '113']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                 list_account_credit, start_date,
                                                                                 end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)
                    if number == '06':
                        list_account_debit =['111', '112']
                        list_account_credit = ['711', '133', '141', '244']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                 list_account_credit, start_date,
                                                                                 end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)
                    if number == '07':
                        list_account_debit =['811', '161', '244', '333', '338', '344', '352', '353', '356']
                        list_account_credit = ['111', '112', '113']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                 list_account_credit, start_date,
                                                                                 end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)
                    if number == '20':
                        list = ['01', '02', '03', '04', '05', '06', '07']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)

                    if number == '21':
                        list_account_credit = ['111', '112', '113']
                        list_account_debit = ['211', '213', '217', '241', '331', '3411']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                 list_account_credit, start_date,
                                                                                 end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)
                    if number == '22':
                        current_year = 0
                        last_year = 0
                        list_account = [
                            [['111', '112', '113'], ['711', '5117', '131']],
                            [['632', '811'], ['111', '112', '113']]
                        ]
                        for list in list_account:
                            current_year += self.get_account_move_from_account(list[0], list[1], start_date, end_date)
                            last_year += self.get_account_move_from_account(list[0], list[1], start_date_l, end_date_l)

                        record.current_year = current_year
                        record.last_year = last_year
                    if number == '23':
                        list_account_credit = ['111', '112', '113']

                        list_account_debit = ['128', '171']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                list_account_credit, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)

                    if number == '24':
                        list_account_debit = ['111', '112', '113']

                        list_account_credit = ['128', '171']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                 list_account_credit, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)
                    if number == '25':
                        list_account_credit = ['111', '112', '113']

                        list_account_debit = ['221', '222', '2281', '131']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                list_account_credit, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)

                    if number == '26':
                        list_account_debit = ['111', '112', '113']

                        list_account_credit = ['221', '222', '2281', '131']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                list_account_credit, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)
                    if number == '27':
                        list_account_debit = ['111', '112', '113']

                        list_account_credit = ['515']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                list_account_credit, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)
                    if number == '30':
                        list = ['21', '22', '23', '24', '25', '26', '27']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)

                    if number == '31':
                        list_account_debit = ['111', '112', '113']

                        list_account_credit = ['411']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                list_account_credit, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)

                    if number == '32':
                        list_account_credit = ['111', '112', '113']

                        list_account_debit = ['411', '419']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                list_account_credit, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)

                    if number == '33':
                        list_account_debit = ['111', '112', '113']

                        list_account_credit = ['171', '3411', '3431', '3432', '41112']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                list_account_credit, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)

                    if number == '34':
                        list_account_credit = ['111', '112', '113']

                        list_account_debit = ['171', '3411', '3431', '3432', '41112']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                list_account_credit, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)
                    if number == '35':
                        list_account_credit = ['111', '112', '113']

                        list_account_debit = ['3412']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                 list_account_credit, start_date,
                                                                                 end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)
                    if number == '36':
                        list_account_credit = ['111', '112', '113']

                        list_account_debit = ['421', '338']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                 list_account_credit, start_date,
                                                                                 end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)
                    if number == '40':
                        list = ['31', '32', '33', '34', '35', '36']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)

                    if number == '50':
                        list = ['20', '30', '40']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '60':
                        current_year = 0
                        last_year = 0
                        list_account = ['111', '112', '113']
                        type_char = 'debit'
                        current_year += self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        last_year += self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)

                        list_account = ['1281', '1288']
                        type_char = 'debit'
                        current_year += self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        last_year += self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                        # list_account_2 = ['1281', '1288']
                        # current_year += self.get_account_move_line_amount(list_account_2, type_char, start_date,
                        #                                                         end_date)
                        # last_year += self.get_account_move_line_amount(list_account_2, type, start_date_l,
                        #                                                      end_date_l)

                        record.current_year = current_year
                        record.last_year  = last_year
                    if number == '61':
                        list_account_debit = ['111', '112', '113']

                        list_account_credit = ['4131']

                        record.current_year = self.get_account_move_from_account(list_account_debit,
                                                                                 list_account_credit, start_date,
                                                                                 end_date)
                        record.last_year = self.get_account_move_from_account(list_account_debit, list_account_credit,
                                                                              start_date_l, end_date_l)
                    if number == '70':
                        list = ['61', '60', '50']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number in ['02', '03', '04', '05', '07', '21', '22', '23', '25', '32', '34', '35', '36', '50', '61']:
                        line['report'] = [number, record.description, "(" + '{0:,.1f}'.format(record.current_year) + ")" if number else "",
                                          "(" + '{0:,.1f}'.format(record.last_year) + ")" if number else ""]
                    else:
                        line['report'] = [number, record.description, '{0:,.1f}'.format(record.current_year) if number else "",
                                          '{0:,.1f}'.format(record.last_year) if number else ""]
            for line in (filter(lambda x: x['level'] == 1, res)):
                if 'id' in line and line['id']:
                    record = self.env['account.financial.html.report.line'].browse(line['id'])
                    number = record.number if record.number else ""
                    # if number == '1':
                    #     current_year = ref.line_ids.children_ids.filtered(lambda s: s.number == '50').current_year
                    #     last_year = ref.line_ids.children_ids.filtered(lambda s: s.number == '50').last_year
                    #
                    #     record.current_year = current_year
                    #     record.last_year = last_year

                    line['report'] = [number, record.description, '{0:,.1f}'.format(record.current_year) if number else "",
                                      '{0:,.1f}'.format(record.last_year) if number else ""]
            for line in (filter(lambda x: x['level'] == 0, res)):
                if 'id' in line and line['id']:
                    record = self.env['account.financial.html.report.line'].browse(line['id'])
                    number = record.number if record.number else ""
                    line['report'] = [number, record.description, '{0:,.1f}'.format(record.current_year) if number else "",
                                      '{0:,.1f}'.format(record.last_year) if number else ""]
        elif self.id == bangcandoi.id:
            for line in (filter(lambda x: x['level'] == 4, res)):
                if 'id' in line and line['id']:
                    record = self.env['account.financial.html.report.line'].browse(line['id'])
                    number = record.number if record.number else ""
                    if number == '222':
                        list_account = ['211']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    if number == '223':
                        list_account = ['2141']
                        type_char = 'credit'
                        record.current_year = - self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = - self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    if number == '225':
                        list_account = ['212']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    if number == '226':
                        list_account = ['2142']
                        type_char = 'credit'
                        record.current_year = - self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = - self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    if number == '228':
                        list_account = ['213']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    if number == '229':
                        list_account = ['2143']
                        type_char = 'credit'
                        record.current_year = - self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = - self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '231':
                        list_account = ['217']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '232':
                        list_account = ['2147']
                        type_char = 'credit'
                        record.current_year = - self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = - self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    if number == '411a':
                        list_account = ['41111']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    if number == '411b':
                        list_account = ['41112']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    if number == '421a':
                        list_account = ['4211']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    if number == '421b':
                        list_account = ['4212']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    line['report'] = [number, "", ('{0:,.1f}'.format(record.current_year) if record.current_year >= 0 else '({0:,.1f})'.format(abs(record.current_year))) if number else "",
                                          ('{0:,.1f}'.format(record.last_year) if record.last_year >= 0 else '({0:,.1f})'.format(abs(record.last_year))) if number else ""]
            for line in (filter(lambda x: x['level'] == 3, res)):
                if 'id' in line and line['id']:
                    record = self.env['account.financial.html.report.line'].browse(line['id'])
                    number = record.number if record.number else ""
                    if number == '111':
                        list_account = ['111', '112', '113']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)
                    elif number == '112':
                        list_account = ['1281', '1288']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)

                    elif number == '121':
                        list_account = ['121']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)

                    elif number == '122':
                        list_account = ['2291']
                        type_char = 'credit'
                        record.current_year = - self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.last_year = - self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)

                    elif number == '123':
                        list_account = ['1281', '1282', '1288']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)

                    elif number == '131':
                        list_account = ['131']
                        type_char = 'debit'
                        # record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        # record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,end_date_l)
                        record.current_year = self.get_debit_ck_from_thcn(list_account, start_date, end_date)
                        record.last_year = self.get_debit_dk_from_thcn(list_account, start_date_l, end_date_l)

                    elif number == '132':
                        list_account = ['331']
                        type_char = 'debit'
                        # record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        # record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)
                        record.current_year = self.get_debit_ck_from_thcn(list_account, start_date, end_date)
                        record.last_year = self.get_debit_dk_from_thcn(list_account, start_date_l, end_date_l)

                    elif number == '133':
                        list_account = ['1362', '1363', '1368']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)

                    elif number =='134':
                        list_account = ['337']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)

                    elif number == '135':
                        list_account = ['1283']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)

                    elif number == '136':
                        list_account = ['1385', '1388', '334', '141', '244', '338'] # '338
                        type_char = 'debit'
                        current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.current_year = current_year if current_year > 0 else 0

                        last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)
                        record.last_year = last_year if last_year > 0 else 0

                    elif number == '137':
                        list_account = ['2293']
                        type_char = 'credit'
                        record.current_year = - self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = - self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)

                    elif number == '139':
                        list_account = ['1381']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)

                    elif number == '141':
                        list_account = ['151', '152', '153', '154', '155', '156', '157', '158']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)


                    elif number == '149':
                        list_account = ['2294']
                        type_char = 'credit'
                        record.current_year = - self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.last_year = - self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)

                    elif number == '151':
                        list_account = ['242']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)

                    elif number == '152':
                        list_account = ['133']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)

                    elif number == '153':
                        list_account = ['333']
                        type_char = 'debit'
                        current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.current_year = current_year if current_year > 0 else 0

                        last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)
                        record.last_year = last_year if last_year > 0 else 0

                    elif number == '154':
                        list_account = ['171']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)

                    elif number == '155':
                        list_account = ['2288']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)

                    elif number == '211':
                        list_account = ['131']
                        type_char = 'debit'

                        record.current_year = 0
                        record.last_year = 0
                        # record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        # record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)

                    elif number == '212':
                        list_account = ['331']
                        type_char = 'debit'

                        # current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        # record.current_year = current_year if current_year > 0 else 0
                        #
                        # last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)
                        # record.last_year = last_year if last_year > 0 else 0
                        record.current_year = 0
                        record.last_year = 0

                    elif number == '213':
                        list_account = ['1361']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '214':
                        list_account = ['1362', '1363', '1368']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '215':
                        list_account = ['1283']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)

                    elif number == '216':
                        list_account = ['1385', '1388', '334', '338', '141', '244']
                        type_char = 'debit'
                        record.current_year = 0
                        record.last_year = 0
                        # current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        # record.current_year = current_year if current_year > 0 else 0
                        #
                        # last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)
                        # record.last_year = last_year if last_year > 0 else 0

                    elif number == '219':
                        list_account = ['2293']
                        type_char = 'credit'
                        record.current_year = - self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = - self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '221':
                        list = ['222', '223']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    elif number == '222':
                        list_account = ['211']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '223':
                        list_account = ['2141']
                        type_char = 'credit'
                        record.current_year = - self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = - self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                        end_date_l)
                    elif number == '224':
                        list = ['225', '226']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    elif number == '225' :
                        list_account = ['212']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '226':
                        list_account = ['2142']
                        type_char = 'credit'
                        record.current_year = - self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = - self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '227':
                        list = ['228', '229']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)

                    elif number == '228':
                        list_account = ['213']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '229':
                        list_account = ['2143',]
                        type_char = 'credit'
                        record.current_year = - self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = - self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '230':
                        list = ['231', '232']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    elif number == '231':
                        list_account = ['217']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,end_date_l)
                    elif number == '232':
                        list_account = ['2147']
                        type_char = 'credit'
                        record.current_year = - self.get_account_move_line_amount(list_account, type_char, start_date,end_date)
                        record.last_year = - self.get_account_move_line_amount(list_account, type_char, start_date_l,end_date_l)
                    elif number == '241':
                        list_account_credit = ['2294']
                        type_char_credit = 'credit'

                        list_account_debit = ['154']
                        type_char_debit = 'debit'

                        record.current_year = self.get_account_move_line_amount(list_account_debit, type_char_debit, start_date, end_date) - self.get_account_move_line_amount(list_account_credit, type_char_credit, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account_debit, type_char_debit, start_date_l, end_date_l) - self.get_account_move_line_amount(list_account_credit, type_char_credit, start_date_l, end_date_l)

                    elif number == '242':
                        list_account = ['241']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)

                    elif number == '251':
                        list_account = ['221']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '252':
                        list_account = ['222']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '253':
                        list_account = ['2281']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '254':
                        list_account = ['2292']
                        type_char = 'credit'
                        record.current_year = - self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = - self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '255':
                        list_account = ['1281', '1282', '1288']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '261':
                        list_account = ['242']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '262':
                        list_account = ['243']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '263':
                        list_account = ['1534', '2294']
                        type_char = 'credit'
                        record.current_year = - self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = - self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '268':
                        list_account = ['2288']
                        type_char = 'debit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '311':
                        list_account = ['331']
                        type_char = 'credit'
                        # record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,end_date)
                        # record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,end_date_l)
                        record.current_year = self.get_credit_ck_from_thcn(list_account, start_date, end_date)
                        record.last_year = self.get_credit_dk_from_thcn(list_account, start_date_l, end_date_l)

                    elif number == '312':
                        list_account = ['131']
                        type_char = 'credit'
                        # current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        # record.current_year = current_year if current_year > 0 else 0
                        #
                        # last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)
                        # record.last_year = last_year if last_year > 0 else 0
                        record.current_year = self.get_credit_ck_from_thcn(list_account, start_date, end_date)
                        record.last_year = self.get_credit_dk_from_thcn(list_account, start_date_l, end_date_l)

                    elif number == '313':
                        list_account = ['333']
                        type_char = 'credit'
                        # current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        # record.current_year = current_year if current_year > 0 else 0
                        record.current_year = self.get_credit_ck_from_thcn(list_account, start_date, end_date)
                        record.last_year = self.get_credit_dk_from_thcn(list_account, start_date_l, end_date_l)

                        # last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)
                        # record.last_year = last_year if last_year > 0 else 0
                    elif number == '314':
                        list_account = ['334']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        # record.current_year = current_year if current_year > 0 else 0

                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)
                        # record.last_year = last_year if last_year > 0 else 0

                    elif number == '315':
                        list_account = ['335']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)

                    elif number == '316':
                        list_account = ['3362', '3363', '3368']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)
                    elif number == '317':
                        list_account = ['337']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '318':
                        list_account = ['3387']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '319':
                        list_account = ['338', '138', '344']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '320':
                        list_account = ['341', '34311']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '321':
                        list_account = ['352']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '322':
                        list_account = ['353']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '323':
                        list_account = ['357']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '324':
                        list_account = ['171']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '331':
                        record.current_year = 0
                        record.last_year = 0
                        list_account = ['331']
                        type_char = 'credit'
                        # record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        # record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)
                    elif number == '332':
                        list_account = ['131']
                        type_char = 'credit'
                        record.current_year = 0
                        record.last_year = 0
                        # current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        # record.current_year = current_year if current_year > 0 else 0
                        #
                        # last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)
                        # record.last_year = last_year if last_year > 0 else 0

                    elif number == '333':
                        list_account = ['335']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '334':
                        list_account = ['3361']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '335':
                        list_account = ['3362', '3363', '3368']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '336':
                        list_account = ['3387']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '337':
                        list_account = ['338', '344']
                        type_char = 'credit'
                        record.current_year = 0
                        record.last_year = 0

                        # record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date, end_date)
                        # record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l, end_date_l)
                    elif number == '338':
                        list_account_credit = ['341', '34311', '34313']
                        type_char_credit = 'credit'

                        list_account_debit = ['34312']
                        type_char_debit = 'debit'

                        record.current_year = self.get_account_move_line_amount(list_account_credit, type_char_credit,
                                                                                start_date,
                                                                                end_date) - self.get_account_move_line_amount(
                            list_account_debit, type_char_debit, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account_credit, type_char_credit,
                                                                             start_date_l,
                                                                             end_date_l) - self.get_account_move_line_amount(
                            list_account_debit, type_char_debit, start_date_l, end_date_l)
                    elif number == '339':
                        list_account = ['3432']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)

                    elif number == '340':
                        list_account = ['41112']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '341':
                        list_account = ['347']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '342':
                        list_account = ['352']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '343':
                        list_account = ['356']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '411':
                        # list_account = ['411']
                        list = ['411a','411b']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                        # type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(['4111'], type_char, start_date, end_date) + record.current_year
                        record.last_year = self.get_account_move_line_amount(['4111'], type_char, start_date_l, end_date_l) + record.last_year
                    # elif number == '411b':
                    #     list_account = ['41112']
                    #     type_char = 'credit'
                    #     record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                    #                                                             end_date)
                    #     record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                    #                                                          end_date_l)
                    # elif number == '411a':
                    #     list_account = ['41111']
                    #     type_char = 'credit'
                    #     record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                    #                                                             end_date)
                    #     record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                    #                                                          end_date_l)
                    elif number == '412':
                        list_account = ['4112']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '413':
                        list_account = ['4113']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '414':
                        list_account = ['4118']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '415':
                        list_account = ['419']
                        type_char = 'debit'
                        record.current_year = - self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = - self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '416':
                        list_account = ['412']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '417':
                        list_account = ['413']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '418':
                        list_account = ['414']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '419':
                        list_account = ['417']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '420':
                        list_account = ['418']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '421':
                        list = ['421a', '421b']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    # elif number == '421a':
                    #     list_account = ['4211']
                    #     type_char = 'credit'
                    #     record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,end_date)
                    #     record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,end_date_l)
                    # elif number == '421b':
                    #     list_account = ['4212']
                    #     type_char = 'credit'
                    #     record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,end_date)
                    #     record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,end_date_l)
                    elif number == '422':
                        list_account = ['441']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)
                    elif number == '431':
                        list_account_credit = ['461']
                        type_char_credit = 'credit'

                        list_account_debit = ['161']
                        type_char_debit = 'debit'

                        record.current_year = self.get_account_move_line_amount(list_account_credit, type_char_credit,
                                                                                start_date,
                                                                                end_date) - self.get_account_move_line_amount(
                            list_account_debit, type_char_debit, start_date, end_date)
                        record.last_year = self.get_account_move_line_amount(list_account_credit, type_char_credit,
                                                                             start_date_l,
                                                                             end_date_l) - self.get_account_move_line_amount(
                            list_account_debit, type_char_debit, start_date_l, end_date_l)
                    elif number == '432':
                        list_account = ['446']
                        type_char = 'credit'
                        record.current_year = self.get_account_move_line_amount(list_account, type_char, start_date,
                                                                                end_date)
                        record.last_year = self.get_account_move_line_amount(list_account, type_char, start_date_l,
                                                                             end_date_l)

                    line['report'] = [number, "", ('{0:,.1f}'.format(record.current_year) if record.current_year >= 0 else '({0:,.1f})'.format(abs(record.current_year))) if number else "",
                                          ('{0:,.1f}'.format(record.last_year) if record.last_year >= 0 else '({0:,.1f})'.format(abs(record.last_year))) if number else ""]
            for line in (filter(lambda x: x['level'] == 2, res)):
                if 'id' in line and line['id']:
                    record = self.env['account.financial.html.report.line'].browse(line['id'])
                    number = record.number if record.number else ""
                    if number == '110':
                        record.current_year = self.get_in_finanial_line(res,
                                                                        '111').current_year + self.get_in_finanial_line(
                            res, '112').current_year
                        record.last_year = self.get_in_finanial_line(res, '111').last_year + self.get_in_finanial_line(
                            res,
                            '112').last_year
                    if number == '120':
                        list = ['121', '122', '123']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '130':
                        list = ['131', '132', '133', '134', '135', '136', '137', '139']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '140':
                        list = ['141', '149']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '150':
                        list = ['151', '152', '153', '154', '155']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '210':
                        list = ['211', '212', '213', '214', '215', '216', '219']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '220':
                        list = ['221', '224', '227']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '230':
                        list = ['231', '232']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '230':
                        list = ['231', '232']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '240':
                        list = ['241', '242']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '250':
                        list = ['251', '252', '253', '254', '255']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '260':
                        list = ['261', '262','263', '268']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '310':
                        list = ['311', '312', '313', '314', '315', '316', '317', '318', '319', '320', '321', '322', '323', '324']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '330':
                        list = ['331', '332', '333', '334', '335', '336', '337', '338', '339', '340', '341', '342', '343']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '410':
                        list = ['411', '412', '413', '414', '415', '416', '417', '418', '419', '420', '421', '422']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '430':
                        list = ['431', '432']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    line['report'] = [number, "", ('{0:,.1f}'.format(record.current_year) if record.current_year >= 0 else '({0:,.1f})'.format(abs(record.current_year))) if number else "",
                                          ('{0:,.1f}'.format(record.last_year) if record.last_year >= 0 else '({0:,.1f})'.format(abs(record.last_year))) if number else ""]
            for line in (filter(lambda x: x['level'] == 1, res)):
                if 'id' in line and line['id']:
                    record = self.env['account.financial.html.report.line'].browse(line['id'])
                    number = record.number if record.number else ""
                    if number == '100':
                        list = ['110', '120', '130', '140', '150']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '200':
                        list = ['210', '220', '230', '240', '250', '260']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '270':
                        list = ['100', '200']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '300':
                        list = ['310', '330']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '400':
                        list = ['410', '430']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    if number == '440':
                        list = ['300', '400']
                        record.current_year, record.last_year = self.sum_current_finanial_line(res, list)
                    line['report'] = [number, "", ('{0:,.1f}'.format(record.current_year) if record.current_year >= 0 else '({0:,.1f})'.format(abs(record.current_year))) if number else "",
                                          ('{0:,.1f}'.format(record.last_year) if record.last_year >= 0 else '({0:,.1f})'.format(abs(record.last_year))) if number else ""]
            for line in (filter(lambda x: x['level'] == 0, res)):
                if 'id' in line and line['id']:
                    record = self.env['account.financial.html.report.line'].browse(line['id'])
                    number = record.number if record.number else ""
                    line['report'] = [number, "", ('{0:,.1f}'.format(record.current_year) if record.current_year >= 0 else '({0:,.1f})'.format(abs(record.current_year))) if number else "",
                                          ('{0:,.1f}'.format(record.last_year) if record.last_year >= 0 else '({0:,.1f})'.format(abs(record.last_year))) if number else ""]
        return res



    def get_template(self):
        res = super(ReportAccountFinancialReport, self).get_template()
        hoatdongkindoanh = self.env.ref('tuanhuy_account_reports.tuanhuy_hoatdong_kinhdoanh_report')
        luuhcuyentiente = self.env.ref('tuanhuy_account_reports.tuanhuy_financial_report_cashsummary0')
        bangcandoi = self.env.ref('tuanhuy_account_reports.account_financial_report_balancesheet0')
        list_report = [hoatdongkindoanh.id, luuhcuyentiente.id, bangcandoi.id]
        if list_report and self.id in list_report:
            return 'tuanhuy_account_reports.report_financial'
        return res

    def get_in_finanial_line(self, res, number):
        result = False
        for line in res:
            if 'id' in line and line['id']:
                record = self.env['account.financial.html.report.line'].browse(line['id'])
                if record.number == number:
                    result = record
        return result
    def sum_current_finanial_line(self, res, list):
        list_number = ['02', '03', '04', '05', '07', '21', '22', '23', '25', '32', '34', '35', '36', '50', '61']
        luuhcuyentiente = self.env.ref('tuanhuy_account_reports.tuanhuy_financial_report_cashsummary0')
        current_year = 0
        last_year = 0
        for number in list:
            for line in res:
                if 'id' in line and line['id']:
                    record = self.env['account.financial.html.report.line'].browse(line['id'])
                    if record.number == number:
                        if self.id == luuhcuyentiente.id and record.number in list_number:
                            current_year -= record.current_year
                            last_year -= record.last_year
                        else:
                            current_year += record.current_year
                            last_year += record.last_year
        return current_year, last_year

    def get_account_move_line_amount(self, list_account, type, start_date, end_date):
        condition = []
        account_list = []
        amount = 0
        aml_obj = self.env['account.move.line']
        for account in list_account:
            account_code_ids = self.env['account.account'].search([('code', '=like', account + '%')])
            for account_code in account_code_ids:
                account_list.append(account_code.code)
        if len(account_list) > 1:
            for i in range(0, len(account_list) - 1):
                condition.append('|')
        for account in account_list:
            condition.append(('account_id.code', '=', account))
        if start_date:
            condition.append(('date', '>=', start_date))
        if end_date:
            condition.append(('date', '<=', end_date))
        if len(account_list) == 0:
            return 0
        journal_items = aml_obj.search(condition)
        if type == 'debit':
            amount = (sum(journal_items.mapped('debit')) - sum(journal_items.mapped('credit'))) if journal_items else 0
        elif type == 'credit':
            amount = (sum(journal_items.mapped('credit')) - sum(journal_items.mapped('debit'))) if journal_items else 0
        # amount = sum(journal_items.mapped(type)) if journal_items else 0
        return amount

    def get_soduno_tk(self, list_account, type, context_id, start_date, end_date):
        if context_id.date_filter == 'custom':
            end_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)
            start_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(months=1)
        elif context_id.date_filter == 'this_month':
            start_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(months=1)
            end_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)
        elif context_id.date_filter == 'this_year':
            start_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(years=1)
            end_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)
        elif context_id.date_filter == 'last_month':
            start_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(months=1)
            end_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)
        elif context_id.date_filter == 'last_quarter':
            start_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(months=3)
            end_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)
        elif context_id.date_filter == 'last_year':
            start_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(years=1)
            end_l = datetime.strptime(start_date, "%Y-%m-%d") - relativedelta(days=1)
        start_date_l = start_l.strftime(DEFAULT_SERVER_DATE_FORMAT)
        end_date_l = end_l.strftime(DEFAULT_SERVER_DATE_FORMAT)
        account_list = []
        conditions = []
        conditions_before = []
        for account in list_account:
            account_code_ids = self.env['account.account'].search([('code', '=like', account + '%')])
            for account_code in account_code_ids:
                account_list.append(account_code.code)
        conditions_before.append(('account_id.code', 'in', account_list))
        if start_date:
            conditions.append(('date', '>=', start_date))
            conditions_before.append(('date', '<', end_date_l))
        if end_date:
            conditions.append(('date', '<=', end_date))
            conditions_before.append(('date', '>=', start_date_l))
        else:
            end_date = fields.Date.today()
            conditions.append(('date', '<=', end_date))
        no_before = 0.0
        co_before = 0.0
        if start_date:
            data_before = self.env['account.move.line'].search(conditions_before)
            for data_line in data_before:
                no_before += data_line.debit
                co_before += data_line.credit
        no_current = 0.0
        co_current = 0.0
        current_data = self.env['account.move.line'].search(conditions)  # , order='partner_id asc, date asc'
        for data_line in current_data:
            no_current += data_line.debit
            co_current += data_line.credit
        # if type == 'debit':
        amount_no = no_current - co_before - co_current
            # return - amount
        # elif type == 'credit':
        amount_co = co_current - no_before - no_current
        return amount_no + amount_co

    def get_account_move_from_account(self, list_debit, list_credit, start_date, end_date):
        condition = []
        list_debit_account = []
        list_credit_account = []
        condition_debit_account = []
        condition_credit_account = []
        if start_date:
            condition.append(('date', '>=', start_date))
        if end_date:
            condition.append(('date', '<=', end_date))

        for account in list_debit:
            account_code_ids = self.env['account.account'].search([('code', '=like', account + '%')])
            for account_code in account_code_ids:
                list_debit_account.append(account_code.code)
        for account in list_credit:
            account_code_ids = self.env['account.account'].search([('code', '=like', account + '%')])
            for account_code in account_code_ids:
                list_credit_account.append(account_code.code)
        if list_debit_account:
            condition_debit_account = condition + [('account_id.code', 'in', list_debit_account), ('debit', '>', 0)]
        if list_credit_account:
            condition_credit_account = condition + [('account_id.code', 'in', list_credit_account), ('credit', '>', 0)]
        move_line_debit = self.env['account.move.line'].search(condition_debit_account)
        move_line_credit = self.env['account.move.line'].search(condition_credit_account)
        if not list_debit_account or not list_credit_account:
            return 0
        if not move_line_debit or not move_line_credit:
            return 0
        am_debit = move_line_debit.mapped('move_id')
        am_credit = move_line_credit.mapped('move_id')
        a = list(set(am_debit).intersection(am_credit))
        if a:
            amount_no = 0
            amount_co = 0
            for move in a:
                for line in move.line_ids:
                    amount_no += line.debit if line.account_id.code in list_debit_account else 0
                    amount_co += line.credit if line.account_id.code in list_credit_account else 0

            return min([amount_no, amount_co])
        else:
            return 0


    def get_luyke_tk(self, list_account, type, start_date, end_date):
        condition = []
        account_list = []
        amount = 0
        aml_obj = self.env['account.move.line']
        for account in list_account:
            account_code_ids = self.env['account.account'].search([('code', '=like', account + '%')])
            for account_code in account_code_ids:
                account_list.append(account_code.code)
        if len(account_list) > 1:
            for i in range(0, len(account_list) - 1):
                condition.append('|')
        for account in account_list:
            condition.append(('account_id.code', '=', account))
        if start_date:
            condition.append(('date', '>=', start_date))
        if end_date:
            condition.append(('date', '<=', end_date))
        if len(account_list) == 0:
            return 0
        journal_items = aml_obj.search(condition)
        amount = sum(journal_items.mapped(type)) if journal_items else 0
        return amount

class AccountFinancialReportLine(models.Model):
    _inherit = "account.financial.html.report.line"

    number = fields.Char()
    current_year = fields.Float()
    last_year = fields.Float()
    description = fields.Char()


class AccountFinancialReportContext(models.TransientModel):
    _inherit = "account.financial.html.report.context"

    def get_columns_names(self):
        res = super(AccountFinancialReportContext, self).get_columns_names()
        ref = self.env.ref('tuanhuy_account_reports.tuanhuy_hoatdong_kinhdoanh_report')
        if self.report_id and self.report_id.id == ref.id:
            res = [unicode('Năm trước', 'utf-8')]
        return res

    def get_columns_names_add(self):
        columns = ['MaSo', 'ThuyetMinh']
        return columns


class AccountReportContextCommon(models.TransientModel):
    _inherit = "account.report.context.common"

    def get_xlsx(self, response):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        report_id = self.get_report_obj()
        sheet = workbook.add_worksheet(report_id.get_title())
        hoatdongkindoanh = self.env.ref('tuanhuy_account_reports.tuanhuy_hoatdong_kinhdoanh_report')
        luuhcuyentiente = self.env.ref('tuanhuy_account_reports.tuanhuy_financial_report_cashsummary0')
        bangcandoi = self.env.ref('tuanhuy_account_reports.account_financial_report_balancesheet0')
        list_report = [hoatdongkindoanh.id, luuhcuyentiente.id, bangcandoi.id]
        if self.report_id and self.report_id.id in list_report:
            tuanhuy_report = self.create_report_financial(sheet, workbook, report_id)
        else:
            def_style = workbook.add_format({'font_name': 'Arial'})
            title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})
            level_0_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'pattern': 1, 'font_color': '#FFFFFF'})
            level_0_style_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'left': 2, 'pattern': 1, 'font_color': '#FFFFFF'})
            level_0_style_right = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'right': 2, 'pattern': 1, 'font_color': '#FFFFFF'})
            level_1_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2})
            level_1_style_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'left': 2})
            level_1_style_right = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'top': 2, 'right': 2})
            level_2_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'top': 2})
            level_2_style_left = workbook.add_format({'font_name': 'Arial', 'bold': True, 'top': 2, 'left': 2})
            level_2_style_right = workbook.add_format({'font_name': 'Arial', 'bold': True, 'top': 2, 'right': 2})
            level_3_style = def_style
            level_3_style_left = workbook.add_format({'font_name': 'Arial', 'left': 2})
            level_3_style_right = workbook.add_format({'font_name': 'Arial', 'right': 2})
            domain_style = workbook.add_format({'font_name': 'Arial', 'italic': True})
            domain_style_left = workbook.add_format({'font_name': 'Arial', 'italic': True, 'left': 2})
            domain_style_right = workbook.add_format({'font_name': 'Arial', 'italic': True, 'right': 2})
            upper_line_style = workbook.add_format({'font_name': 'Arial', 'top': 2})

            sheet.set_column(0, 0, 1000) #  Set the first column width to 1000

            sheet.write(0, 0, '', title_style)

            y_offset = 0
            if self.get_report_obj().get_name() == 'coa' and self.get_special_date_line_names():
                sheet.write(y_offset, 0, '', title_style)
                sheet.write(y_offset, 1, '', title_style)
                x = 2
                for column in self.with_context(is_xls=True).get_special_date_line_names():
                    sheet.write(y_offset, x, column, title_style)
                    sheet.write(y_offset, x+1, '', title_style)
                    x += 2
                sheet.write(y_offset, x, '', title_style)
                y_offset += 1

            x = 1
            for column in self.with_context(is_xls=True).get_columns_names():
                sheet.write(y_offset, x, column.replace('<br/>', ' '), title_style)
                x += 1
            y_offset += 1

            lines = report_id.with_context(no_format=True, print_mode=True).get_lines(self)

            if lines:
                max_width = max([len(l['columns']) for l in lines])

            for y in range(0, len(lines)):
                if lines[y].get('level') == 0 and lines[y].get('type') == 'line':
                    for x in range(0, len(lines[y]['columns']) + 1):
                        sheet.write(y + y_offset, x, None, upper_line_style)
                    y_offset += 1
                    style_left = level_0_style_left
                    style_right = level_0_style_right
                    style = level_0_style
                elif lines[y].get('level') == 1 and lines[y].get('type') == 'line':
                    for x in range(0, len(lines[y]['columns']) + 1):
                        sheet.write(y + y_offset, x, None, upper_line_style)
                    y_offset += 1
                    style_left = level_1_style_left
                    style_right = level_1_style_right
                    style = level_1_style
                elif lines[y].get('level') == 2:
                    style_left = level_2_style_left
                    style_right = level_2_style_right
                    style = level_2_style
                elif lines[y].get('level') == 3:
                    style_left = level_3_style_left
                    style_right = level_3_style_right
                    style = level_3_style
                elif lines[y].get('type') != 'line':
                    style_left = domain_style_left
                    style_right = domain_style_right
                    style = domain_style
                else:
                    style = def_style
                    style_left = def_style
                    style_right = def_style
                sheet.write(y + y_offset, 0, lines[y]['name'], style_left)
                for x in xrange(1, max_width - len(lines[y]['columns']) + 1):
                    sheet.write(y + y_offset, x, None, style)
                for x in xrange(1, len(lines[y]['columns']) + 1):
                    if isinstance(lines[y]['columns'][x - 1], tuple):
                        lines[y]['columns'][x - 1] = lines[y]['columns'][x - 1][0]
                    if x < len(lines[y]['columns']):
                        sheet.write(y + y_offset, x+lines[y].get('colspan', 1)-1, lines[y]['columns'][x - 1], style)
                    else:
                        sheet.write(y + y_offset, x+lines[y].get('colspan', 1)-1, lines[y]['columns'][x - 1], style_right)
                if lines[y]['type'] == 'total' or lines[y].get('level') == 0:
                    for x in xrange(0, len(lines[0]['columns']) + 1):
                        sheet.write(y + 1 + y_offset, x, None, upper_line_style)
                    y_offset += 1
            if lines:
                for x in xrange(0, max_width+1):
                    sheet.write(len(lines) + y_offset, x, None, upper_line_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def get_pdf(self):
        # As the assets are generated during the same transaction as the rendering of the
        # templates calling them, there is a scenario where the assets are unreachable: when
        # you make a request to read the assets while the transaction creating them is not done.
        # Indeed, when you make an asset request, the controller has to read the `ir.attachment`
        # table.
        # This scenario happens when you want to print a PDF report for the first time, as the
        # assets are not in cache and must be generated. To workaround this issue, we manually
        # commit the writes in the `ir.attachment` table. It is done thanks to a key in the context.
        if not config['test_enable']:
            self = self.with_context(commit_assetsbundle=True)

        hoatdongkindoanh = self.env.ref('tuanhuy_account_reports.tuanhuy_hoatdong_kinhdoanh_report')
        luuhcuyentiente = self.env.ref('tuanhuy_account_reports.tuanhuy_financial_report_cashsummary0')
        bangcandoi = self.env.ref('tuanhuy_account_reports.account_financial_report_balancesheet0')
        list_report = [hoatdongkindoanh.id, luuhcuyentiente.id, bangcandoi.id]

        report_obj = self.get_report_obj()
        lines = report_obj.with_context(print_mode=True).get_lines(self)
        footnotes = self.get_footnotes_from_lines(lines)
        base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env[
            'ir.config_parameter'].sudo().get_param('web.base.url')
        rcontext = {
            'mode': 'print',
            'base_url': base_url,
            'company': self.env.user.company_id,
        }
        if self.report_id and self.report_id.id in list_report:
            body = self.env['ir.ui.view'].render_template(
                "tuanhuy_account_reports.report_financial_letter",
                values=dict(rcontext, lines=lines, footnotes=footnotes, report=report_obj, context=self),
            )
        else:
            body = self.env['ir.ui.view'].render_template(
                "account_reports.report_financial_letter",
                values=dict(rcontext, lines=lines, footnotes=footnotes, report=report_obj, context=self),
            )

        header = self.env['report'].render(
            "report.internal_layout",
            values=rcontext,
        )
        header = self.env['report'].render(
            "report.minimal_layout",
            values=dict(rcontext, subst=True, body=header),
        )

        landscape = False
        if len(self.get_columns_names()) > 4:
            landscape = True

        return self.env['report']._run_wkhtmltopdf([header], [''], [(0, body)], landscape,
                                                   self.env.user.company_id.paperformat_id,
                                                   spec_paperformat_args={'data-report-margin-top': 10,
                                                                          'data-report-header-spacing': 10})

    def create_report_financial(self, worksheet, workbook, report_id):
        worksheet.set_column('A:A', 50)
        worksheet.set_column('B:B', 30)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        title = workbook.add_format(
            {'bold': True, 'font_size': '18', 'align': 'center', 'valign': 'vcenter'})
        header_table_color = workbook.add_format(
            {'bold': True, 'border': 0, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        header_table_name = workbook.add_format(
            {'bold': True, 'border': 0, 'font_size': '14', 'align': 'left', 'valign': 'vcenter'})
        header_table_number = workbook.add_format(
            {'bold': False, 'border': 0, 'font_size': '14', 'align': 'right', 'valign': 'vcenter'})
        money = workbook.add_format(
            {'bold': False, 'border': 0, 'font_size': '14', 'align': 'right', 'valign': 'vcenter','num_format': '#,##0',})
        header_table_str = workbook.add_format(
            {'bold': False, 'border': 0, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        back_color = 'A1:E1'
        worksheet.merge_range(back_color, unicode("BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH", "utf-8"), title)
        worksheet.merge_range('A2:E2', unicode("Năm......", "utf-8"), header_table_color)

        row = 4
        worksheet.merge_range(row, 0, row, 1, 'CHỈ TIÊU', header_table_color)
        summary_header = ['Mã số', 'Thuyết minh', 'Năm nay', 'Năm trước']
        [worksheet.write(row, 2 + header_cell, summary_header[header_cell], header_table_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
        row += 1
        worksheet.merge_range(row, 0, row, 1, '1', header_table_color)
        summary_header = ['2', '3', '4', '5']
        [worksheet.write(row, 2 +header_cell, summary_header[header_cell], header_table_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]
        lines = report_id.with_context(no_format=True, print_mode=True).get_lines(self)
        for line in lines:
            if 'id' in line:
                row += 1
                worksheet.merge_range(row, 0, row, 1, line['name'] if line['name'] else "", header_table_name)
                y_offset = 2
                for col in line['report']:
                    worksheet.write(row, y_offset, col, header_table_number)
                    if col.replace('.','').replace(',','').isdigit():
                        worksheet.write(row, y_offset, float(col.replace(',','')), money)
                    y_offset += 1

        row += 1
        worksheet.write(row, 5, 'Lập, ngày ... tháng ... năm ...', header_table_number)
        row += 1
        worksheet.write(row, 0, 'Người lập biểu', header_table_color)
        worksheet.merge_range(row, 1, row, 2, 'Kế toán trưởng', header_table_color)
        worksheet.merge_range(row, 3, row, 5, 'Giám đốc', header_table_color)
        row += 1
        worksheet.write(row, 0, '(Ký, họ tên)', header_table_str)
        worksheet.merge_range(row, 1, row, 2, '(Ký, họ tên)', header_table_str)
        worksheet.merge_range(row, 3, row, 5, '(Ký, họ tên, đóng dấu)', header_table_str)


