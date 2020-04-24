# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools

class CongNoPhaitra(models.Model):

    _name        = 'cong.no.phaitra'
    _description = 'Cong No 331 Chi Tiet'
    _auto        = False
    _order       = 'date asc, id asc'

    date          = fields.Date('Ngày hạch toán')
    confirm_date  = fields.Date('Ngày chứng từ')
    ref           = fields.Char('Số chứng từ')
    ref_purchase_order = fields.Many2one('purchase.order', string="Số chứng từ", compute="_get_ref_purchase_order")
    ref_account_voucher = fields.Many2one('account.voucher', string="Số chứng từ", compute="_get_ref_account_voucher")
    ref_account_payment_unc = fields.Many2one('account.payment.unc', string="Số chứng từ",
                                              compute="_get_ref_account_payment_unc")
    description   = fields.Char('Diễn giải')
    product_code  = fields.Char('Mã hàng')
    product_qty   = fields.Float('SL')
    price_unit    = fields.Float('Đơn giá')
    account_code  = fields.Char('TK', related='account_id.code')
    account_id    = fields.Many2one('account.account', 'TK')
    account_du    = fields.Char('TK đối ứng', related='account_du_id.code')
    account_du_id = fields.Many2one('account.account', 'TK đối ứng')
    partner_id    = fields.Many2one('res.partner', 'Đối tác')
    debit         = fields.Float('PS Nợ')
    credit        = fields.Float('PS Có')
    debit_after   = fields.Float('Dư Nợ', compute='_compute_after')
    credit_after  = fields.Float('Dư Có', compute='_compute_after')
    voucher_type = fields.Selection([('sale', 'Sale'), ('purchase', 'Purchase')], string='Type',
                                    compute='get_voucher_type')

    @api.depends('ref')
    def get_voucher_type(self):
        for record in self:
            if record.ref:
                account_voucher_id = self.env['account.voucher'].search([('number_voucher', '=', record.ref)], limit=1)
                if account_voucher_id:
                    record.voucher_type = account_voucher_id.voucher_type

    @api.multi
    def _get_ref_purchase_order(self):
        for record in self:
            if record.account_du_id.code in ['1331', '3381', '5213'] and record.ref:
                sale_id = self.env['purchase.order'].search([('name', '=', record.ref)])
                if sale_id:
                    record.ref_purchase_order = sale_id[0]

    @api.multi
    def _get_ref_account_voucher(self):
        for record in self:
            if record.account_du_id.code in ['1111', '1121'] and record.ref:
                voucher_id = self.env['account.voucher'].search([('number_voucher', '=', record.ref),('voucher_type','=','purchase')])
                if voucher_id:
                    record.ref_account_voucher = voucher_id[0]

    @api.multi
    def _get_ref_account_payment_unc(self):
        for record in self:
            if record.account_du_id.code in ['1111', '1121'] and record.ref:
                gbn_id = self.env['account.payment.unc'].search([('ref', '=', record.ref)])
                if gbn_id:
                    record.ref_account_payment_unc = gbn_id[0]

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        context = self._context.copy() or {}
        if domain:
            context.update({'args': domain})
        res = super(CongNoPhaitra, self.with_context(context)).search_read(domain=domain, fields=fields, offset=offset,
                                                                           limit=limit, order=order)
        return res

    @api.multi
    def _compute_after(self):
        partner_id = False
        args = False
        date = False
        if self._context.get('args', False):
            args = self._context.get('args', False)
        if args and any(['partner_id' in a for a in args]):
            partner = [x for x in args if 'partner_id' in x]
            partner_id = list(partner[0][2])
        for record in self:
            no_before, co_before = record._get_debit_credit_before_to_331(partner_id, date)
            sum_amount = no_before + record.debit - co_before - record.credit
            if sum_amount > 0:
                record.debit_after = sum_amount
                record.credit_after = 0
            else:
                record.debit_after = 0
                record.credit_after = -sum_amount

    @api.model
    def _get_debit_credit_before_to_331(self, partner_id, date):
        no_before = co_before = 0
        no_before_value = co_before_value = 0
        if self.date:
            # get debit before,credit before
            query3 = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                   FROM account_move_line aml 
                                   WHERE aml.account_id = '%s' AND aml.date < '%s' """ % (self.account_id.id, self.date)
            if partner_id:
                query3 += 'AND aml.partner_id in (%s) ' % (', '.join(str(id) for id in partner_id))
            self.env.cr.execute(query3)
            move_before = self.env.cr.fetchall()
            if move_before[0] and (move_before[0][0] or move_before[0][1]):
                no_before = move_before[0][0]
                co_before = move_before[0][1]

            # filter record with date same
            query1 = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                                                    FROM cong_no_phaitra aml
                                                                    WHERE aml.date = '%s' AND aml.id < '%s' """ % (self.date, self.id)
            if partner_id:
                query1 += 'AND aml.partner_id in (%s) ' % (', '.join(str(id) for id in partner_id))
            self.env.cr.execute(query1)
            move_before1 = self.env.cr.fetchall()
            if move_before1[0] and (move_before1[0][0] or move_before1[0][1]):
                no_before += move_before1[0][0]
                co_before += move_before1[0][1]

            if (no_before - co_before) > 0:
                no_before_value = no_before - co_before
                co_before_value = 0
            else:
                no_before_value = 0
                co_before_value = co_before - no_before
        return no_before_value, co_before_value

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'cong_no_phaitra')
        account_331 = self.env.ref('l10n_vn.chart331')
        query = """
            CREATE VIEW cong_no_phaitra AS (
                SELECT
                    aml2.id as id,
                    aml.date as date,
                    aml.date as confirm_date,
                    am.ref as ref,
                    aml2.name as description,
                    p.default_code as product_code,
                    aml2.quantity as product_qty,
                    ABS(aml2.balance) / aml2.quantity as price_unit,
                    aml.account_id as account_id,
                    aml2.account_id as account_du_id,
                    aml.partner_id as partner_id,
                    aml2.credit as debit,
                    aml2.debit as credit
                FROM
                    account_move_line aml
                INNER JOIN
                    account_move am
                ON
                    aml.move_id = am.id
                INNER JOIN
                    account_move_line aml2
                ON
                    aml2.move_id = am.id
                    AND aml2.id != aml.id
                LEFT JOIN
                    product_product p
                ON
                    aml2.product_id = p.id
                WHERE
                    (am.ref LIKE '%s' OR am.ref LIKE '%s')
                    AND aml.account_id = %s
                UNION ALL (
                    SELECT
                        aml.id as id,
                        aml.date as date,
                        aml.date as confirm_date,
                        am.ref as ref,
                        aml2.name as description,
                        p.default_code as product_code,
                        aml2.quantity as product_qty,
                        CASE
                            WHEN ABS(aml2.balance) > ABS(aml.balance) THEN ABS(aml.balance)
                            ELSE ABS(aml2.balance)
                        END AS price_unit,
                        aml.account_id as account_id,
                        aml2.account_id as account_du_id,
                        aml.partner_id as partner_id,
                        CASE
                            WHEN aml2.credit > aml.debit THEN aml.debit
                            ELSE aml2.credit
                        END AS debit,
                        CASE
                            WHEN aml2.debit > aml.credit THEN aml.credit
                            ELSE aml2.debit
                        END AS credit
                    FROM
                        account_move_line aml
                    INNER JOIN
                        account_move am
                    ON
                        aml.move_id = am.id
                    INNER JOIN
                        account_move_line aml2
                    ON
                        aml2.move_id = am.id
                        AND aml2.account_id != %s
                    LEFT JOIN
                        product_product p
                    ON
                        aml2.product_id = p.id
                    WHERE
                        (am.ref IS NULL OR (am.ref NOT LIKE '%s' AND am.ref NOT LIKE '%s'))
                        AND ((aml.debit > 0 AND aml2.credit > 0) OR (aml.credit > 0 AND aml2.debit > 0))
                        AND aml.account_id = %s
                )
            )""" % ('PO%', 'RTP%', account_331.id, account_331.id, 'PO%', 'RTP%', account_331.id)
        self._cr.execute(query)