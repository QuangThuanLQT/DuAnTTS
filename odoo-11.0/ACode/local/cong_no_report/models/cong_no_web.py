# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools

class CongNoWebReport(models.Model):

    _name = "congno.web.report"
    _description = "Bao Cao Cong No"
    _auto = False

    name = fields.Char('Sản phẩm')
    date = fields.Date('Ngày hạch toán')
    confirm_date = fields.Date('Ngày chứng từ')
    move_id = fields.Many2one('account.move', 'Số chứng từ')
    move_line_id = fields.Many2one('account.move.line', 'Số chứng từ')
    account_code = fields.Char('TK Công nợ')
    partner_id = fields.Many2one('res.partner', 'Khách hàng')
    debit = fields.Float('Debit Phát sinh')
    credit = fields.Float('Credit Phát sinh')
    debit_before = fields.Float('Debit Số dư')
    credit_before = fields.Float('Credit Số dư')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res =  super(CongNoWebReport, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

        if 'debit' in fields and 'credit' in fields:
            no_before = 0.0
            co_before = 0.0

            account_id = self.env['account.account'].search([('code', '=', '131')], limit=1)
            account_code = account_id.code
            conditions_before = [('account_id.code', 'ilike', account_code)]
            date_domain = False
            for sub_dom in domain:
                if 'confirm_date' in sub_dom[0]:
                    sub_dom[0], sub_dom[2] = 'date', sub_dom[2][:10]
                if sub_dom[0] == 'date':
                    date_domain = ('date', '<', sub_dom[2])

            conditions_before.append(date_domain)

            move_lines = self.env['account.move.line'].search(conditions_before, order='date asc')

            for move_line in move_lines:
                no_before += move_line.debit
                co_before += move_line.credit

            for line in res:
                if 'debit' not in line or 'credit' not in line:
                    continue
                debit = line['debit'] or 0
                credit = line['credit'] or 0
                if no_before > 0:
                    no_before += (debit - credit)
                    if no_before < 0:
                        co_before -= no_before
                        no_before = 0
                elif co_before > 0:
                    co_before += (credit - debit)
                    if co_before < 0:
                        no_before -= co_before
                        co_before = 0
                else:
                    no_before += (debit - credit)
                    if no_before < 0:
                        co_before -= no_before
                        no_before = 0
                line['debit_before'] = no_before
                line['credit_before'] = co_before

        return res


    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'congno_web_report')
        account = self.env.ref('l10n_vn.chart131')
        account_id = 131 or account
        self._cr.execute("""
            CREATE VIEW congno_web_report AS (
                SELECT
                    aml.id as id,
                    aml.name as name,
                    aml.id as move_line_id,
                    aml.date as date,
                    aml.date as confirm_date,
                    aml.partner_id as partner_id,
                    aml.move_id as move_id,
                    aa.code as account_code,
                    aml.debit as debit,
                    aml.credit as credit,
                    aml.debit as debit_before,
                    aml.credit as credit_before
                    
                FROM
                    account_move_line as aml
                LEFT JOIN
                    account_move as am ON am.id = aml.move_id
                LEFT JOIN
                    account_account as aa ON aa.id = aml.account_id
                WHERE aa.code = '%s'
            )""" %(account_id))
#GROUP BY aml.id, aa.code, aml.debit, aml.credit