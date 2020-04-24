# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from datetime import timedelta, datetime
import base64
import StringIO
import xlsxwriter
import sys

reload(sys)
sys.setdefaultencoding('utf-8')


class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.model
    def get_stock_am_kho(self, field, start_date, end_date):
        if not end_date:
            end_date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            field = 'date'
        else:
            end_date = datetime.strptime(end_date,'%d/%m/%Y').strftime(DEFAULT_SERVER_DATE_FORMAT)+" 23:59:59"
        if start_date:
            start_date = datetime.strptime(start_date, '%d/%m/%Y').strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        stock_move_id_list = []
        query = """SELECT DISTINCT product_id FROM public.stock_move WHERE %s <= '%s' GROUP BY product_id""" % (
            field, end_date)
        if start_date:
            query = """SELECT DISTINCT product_id FROM public.stock_move WHERE %s >= '%s' AND %s <= '%s' GROUP BY product_id""" % (
                field, start_date, field, end_date)
        self.env.cr.execute(query)
        product_ids = self.env.cr.fetchall()
        if product_ids and len(product_ids) > 0:
            for product_id in product_ids:
                query_st = """SELECT id FROM public.stock_move WHERE product_id=%s AND %s <= '%s' ORDER BY %s DESC, id DESC LIMIT 1""" % (
                    product_id[0], field, end_date, field)
                if start_date:
                    query_st = """SELECT id FROM public.stock_move WHERE product_id=%s AND %s >= '%s' AND %s <= '%s' ORDER BY %s DESC, id DESC LIMIT 1""" % (
                        product_id[0], field, start_date, field, end_date, field)
                self.env.cr.execute(query_st)
                stock_move_id = self.env.cr.fetchall()
                if stock_move_id and len(stock_move_id) > 0 and stock_move_id[0] and stock_move_id[0][0]:
                    quantity_du_bao = self.env['stock.move'].browse(stock_move_id[0][0]).quantity_du_bao
                    if float_compare(quantity_du_bao,0,2) < 0:
                        stock_move_id_list.append(stock_move_id[0][0])
        return stock_move_id_list


class account_move(models.Model):
    _inherit = 'account.move'
    _order = "date ASC, ref ASC"

    @api.multi
    def write(self,vals):
        res = super(account_move, self).write(vals)
        for record in self:
            if len(record.line_ids) > 1 and '1121' in record.line_ids.mapped('account_id').mapped('code'):
                record.line_ids.get_account_doi_ung_1121()
        return res

class account_move_detal(models.TransientModel):
    _name = 'account.move.detail'

    account_id = fields.Many2one('account.account', string='Tài Khoản', required=True)
    start_date = fields.Date(String='Từ Ngày', required=True)
    end_date = fields.Date(String='Đến Ngày')
    partner_id = fields.Many2one('res.partner', 'Đối tác')

    account_move_line_ids = fields.Many2many('account.move.line')
    no_before = fields.Float('Nợ đầu kỳ', readonly=True)
    co_before = fields.Float('Có đầu kỳ', readonly=True)

    # @api.onchange('account_id', 'start_date', 'end_date', 'partner_id')
    def return_acction_report(self):
        self.ensure_one()

        self.account_move_line_ids = False
        condition = []
        condition_before = []
        query = """SELECT 
                            SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                        FROM account_move_line aml 
                        WHERE aml.account_id = '%s' AND aml.date < '%s' """ % (self.account_id.id, self.start_date)
        if self.start_date:
            condition.append(('date', '>=', self.start_date))
            condition_before.append(('date', '<', self.start_date))
        if self.end_date:
            condition.append(('date', '<=', self.end_date))
        if self.partner_id:
            condition.append(('partner_id', '=', self.partner_id.id))
            condition_before.append(('partner_id', '=', self.partner_id.id))
            query += "AND aml.partner_id = '%s' " % (self.partner_id.id)
        condition.append(('account_id', '=', self.account_id.id))
        condition_before.append(('account_id', '=', self.account_id.id))

        no_before = co_before = 0
        self.env.cr.execute(query)
        move_before = self.env.cr.fetchall()
        if move_before and len(move_before) > 0:
            if move_before[0][0] and move_before[0][1]:
                no_before = move_before[0][0]
                co_before = move_before[0][1]
        if (no_before - co_before) > 0:
            self.no_before = no_before - co_before
            self.co_before = 0
        else:
            self.no_before = 0
            self.co_before = co_before - no_before

        # action = self.env.ref('account.action_account_moves_all_a').read()[0]
        # action['domain'] = condition
        # action['name'] = 'Báo Cáo Chi Tiết Tài Khoản'
        # return action


        moves = self.env['account.move.line'].search(condition)
        if moves:
            self.account_move_line_ids = moves

        return {
            "type": "ir.actions.do_nothing",
        }


class account_move_line(models.Model):
    _inherit = 'account.move.line'

    so_du_no = fields.Float(string="Số dư nợ", compute="get_so_du")
    so_du_co = fields.Float(string="Số dư có", compute="get_so_du")
    name_sub = fields.Char(string="Nhãn", compute="_get_name_sub")
    product_default_code = fields.Char(string="Mã nội bộ", compute="_get_product_id")
    product_name = fields.Char(string="Sản phẩm", compute="_get_product_id")
    product_price = fields.Float(string="Đơn giá", compute="_get_product_price")
    account_sub_code = fields.Char(string="Tài khoản", related="account_id.code")
    account_doi_ung_1121 = fields.Boolean(compute="get_account_doi_ung_1121", store=True)
    ref_156_sub = fields.Char(compute="get_ref_156_sub",string="Tham chiếu")
    voucher_type = fields.Selection([('sale', 'Sale'), ('purchase', 'Purchase')], string='Type', compute='get_voucher_type')
    luy_ke_112  = fields.Float('Luỹ kế', compute="get_luyke")

    def get_luyke(self):
        partner_id = False
        args = False
        account_id = []
        move_line_ids = []
        domain_not_date = []
        if self._context.get('args', False):
            args = self._context.get('args', False)
            domain_not_date = self._context.get('args', False)
        if domain_not_date and any(['date' in a for a in args]):
            domain_not_date = filter(lambda rec: rec[0] != 'date', domain_not_date)
        # if args and any(['partner_id' in a for a in args]):
        #     partner = [x for x in args if 'partner_id' in x]
        #     if type(partner[0][2]) is int:
        #         partner_id = [partner[0][2]]
        #     elif type(partner[0][2]) is unicode:
        #         parnter_ids = self.env['res.partner'].search([('name', 'ilike', partner[0][2])])
        #         partner_id = parnter_ids.ids
        #     else:
        #         partner_id = list(partner[0][2])
        # if args and any(['account_id.code' in a for a in args]):
        #     for domain in args:
        #         if 'account_id.code' in domain:
        #             account_list = self.env['account.account'].search([('code', domain[1], domain[2])])
        #             for account in account_list:
        #                 account_id.append(account.id)
        # elif args and any(['account_id' in a for a in args]):
        #     for domain in args:
        #         if 'account_id' in domain:
        #             account_list = self.env['account.account'].search([('code', domain[1], domain[2])])
        #             for account in account_list:
        #                 account_id.append(account.id)
        # if args and any(['account_doiung' in a for a in args]):
        #     for domain in args:
        #         if 'account_doiung' in domain:
        #             account_list = self.env['account.move.line'].search([('account_doiung', domain[1], domain[2])])
        #             for account in account_list:
        #                 move_line_ids.append(account.id)
        #
        # if args and any(['id' in a for a in args]):
        #     line_ids = [x for x in args if 'id' in x]
        #     if type(line_ids[0][2]) is list:
        #         move_line_ids.append(move_id for move_id in line_ids[0][2])

        move_line_ids = self.env['account.move.line'].search(args).ids
        before_move = self.env['account.move.line'].search(domain_not_date)
        for record in self:
            no_before, co_before = record.with_context(luy_ke_before=before_move.ids).calculate_luy_ke_amount(partner_id,account_id,move_line_ids)
            sum_amount = no_before + record.debit - co_before - record.credit
            record.luy_ke_112 = abs(sum_amount)

    @api.model
    def calculate_luy_ke_amount(self, partner_id, account_id, move_line_ids):
        no_before = co_before = 0
        no_before_value = co_before_value = 0
        if self.date:
            query = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                                    FROM account_move_line aml 
                                                    WHERE aml.date < '%s' """ % (self.date)
            # if self.date:
            #     query += "AND account_doiung LIKE '112%' "
            # if account_id:
            #     query += 'AND aml.account_id in (%s) ' % (', '.join(str(id) for id in account_id))
            # if partner_id:
            #     query += 'AND aml.partner_id in (%s) ' % (', '.join(str(id) for id in partner_id))
            # if move_line_ids and len(move_line_ids):
            #     query += 'AND id in (%s) ' % (', '.join(str(id) for id in move_line_ids))
            if self.env.context.get('luy_ke_before',False):
            # if move_line_ids and len(move_line_ids)
                query += 'AND id in (%s) ' % (', '.join(str(id) for id in self.env.context.get('luy_ke_before',False)))
            self.env.cr.execute(query)
            move_before = self.env.cr.fetchall()
            if move_before[0] and (move_before[0][0] or move_before[0][1]):
                no_before = move_before[0][0]
                co_before = move_before[0][1]
            if account_id != self.env['account.account'].search([('code', '=', '1111')], limit=1).ids:
                query1 = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                                                    FROM account_move_line aml 
                                                                    WHERE aml.date = '%s' AND aml.id < '%s' """ % (self.date, self.id)

            else:
                query1 = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                                                                    FROM account_move_line aml 
                                                                                    WHERE aml.date = '%s' AND aml.ref < '%s' """ % (self.date, self.ref)
            # query1 += "AND account_doiung LIKE '112%' "
            # if account_id:
            #     query1 += 'AND aml.account_id in (%s) ' % (', '.join(str(id) for id in account_id))
            # if partner_id:
            #     query1 += 'AND aml.partner_id in (%s) ' % (', '.join(str(id) for id in partner_id))
            if move_line_ids and len(move_line_ids):
                query1 += 'AND id in (%s) ' % (', '.join(str(id) for id in move_line_ids))
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


    @api.model
    def compute_profit_percent(self,domain_list, start_date, end_date, partner_str,context):
        account_code = False
        partner_ids = False
        sale_id = account_id = account_ids = move_id = False
        line_obj = self.env['account.move.line']
        ref = product_code = False
        for domain in domain_list:
            if 'account_id.code' in domain:
                account_code = domain[2]
            elif 'account_doi_ung_1121' in domain:
                account_code = '1121'
            if 'product_id' in domain:
                product_code = domain[2]
            if 'ref' in domain:
                ref = domain[2]
            if 'move_id' in domain:
                ref = domain[2]
        if account_code:
            if '%' in account_code:
                account_ids = self.env['account.account'].search([('code', '=like', account_code)])
            else:
                account_id = self.env['account.account'].search([('code', '=', account_code)],limit=1) if account_code else False

        # if context and context.get('active_model',False) == 'sale.order' and context.get('active_ids',False):
        #     sale_id = self.env['sale.order'].browse(context.get('active_ids',False))
        if start_date:
            start_date_type = datetime.strptime(start_date,'%d/%m/%Y').strftime(DEFAULT_SERVER_DATE_FORMAT)
            domain_list.append(('date','>=',start_date_type))
        if end_date:
            end_date_type = datetime.strptime(end_date, '%d/%m/%Y').strftime(DEFAULT_SERVER_DATE_FORMAT)
            domain_list.append(('date','<=',end_date_type))
        if partner_str:
            customer_ids = []
            name_upper = partner_str.upper()
            self.env.cr.execute(
                "select id from res_partner where upper(name) = '%s'" % (name_upper))
            res_trans = self.env.cr.fetchall()
            for line in res_trans:
                customer_ids.append(line[0])
            domain_list.append(('partner_id', 'in', customer_ids))

        move_line_ids = line_obj.search(domain_list)
        profit = sum(move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('511') or rec.account_id.code.startswith('711')).mapped('credit'))
        loss = sum(move_line_ids.filtered(lambda rec:rec.account_id.code.startswith('632') or rec.account_id.code.startswith('641') or rec.account_id.code.startswith('642') or rec.account_id.code.startswith('811')
                                                     or rec.account_id.code.startswith('622') or rec.account_id.code.startswith('627')).mapped('debit'))
        if profit  != 0:
            return (profit - loss)*100/profit
        else:
            return -100


    @api.depends('ref')
    def get_voucher_type(self):
        for record in self:
            if record.ref:
                account_voucher_id = self.env['account.voucher'].search([('number_voucher', '=', record.ref)], limit=1)
                if account_voucher_id:
                    record.voucher_type = account_voucher_id.voucher_type


    ref_purchase_order = fields.Many2one('purchase.order', string="Số chứng từ", compute="_get_ref_purchase_order")
    ref_account_voucher = fields.Many2one('account.voucher', string="Số chứng từ", compute="_get_ref_account_voucher")
    ref_account_payment_unc = fields.Many2one('account.payment.unc', string="Số chứng từ",
                                              compute="_get_ref_account_payment_unc")
    ref_sale_order = fields.Many2one('sale.order', string="Số chứng từ", compute="_get_ref_sale_order")
    ref_account_payment_gbn = fields.Many2one('account.payment.gbn', string="Số chứng từ",
                                              compute="_get_ref_account_payment_gbn")

    @api.multi
    def _get_ref_sale_order(self):
        for record in self:
            if record.ref:
                sale_id = self.env['sale.order'].search(['|',('name', '=', record.ref),('name','=',record.ref_156_sub)])
                if sale_id:
                    record.ref_sale_order = sale_id[0]

    @api.multi
    def _get_ref_account_voucher(self):
        for record in self:
            if record.ref:
                voucher_id = self.env['account.voucher'].search(
                    [('move_id', '=', record.move_id.id)])
                if voucher_id:
                    record.ref_account_voucher = voucher_id[0]

    @api.multi
    def _get_ref_account_payment_gbn(self):
        for record in self:
            if record.ref:
                gbn_id = self.env['account.payment.gbn'].search([('ref', '=', record.ref)])
                if gbn_id:
                    record.ref_account_payment_gbn = gbn_id[0]

    @api.multi
    def _get_ref_purchase_order(self):
        for record in self:
            if record.ref:
                sale_id = self.env['purchase.order'].search(['|',('name', '=', record.ref),('name','=',record.ref_156_sub)])
                if sale_id:
                    record.ref_purchase_order = sale_id[0]

    @api.multi
    def _get_ref_account_payment_unc(self):
        for record in self:
            if record.ref:
                gbn_id = self.env['account.payment.unc'].search([('ref', '=', record.ref)])
                if gbn_id:
                    record.ref_account_payment_unc = gbn_id[0]

    def get_ref_156_sub(self):
        for record in self:
            stock_picking_id = self.env['stock.picking'].search([('name','=',record.ref)])
            if stock_picking_id and stock_picking_id.origin:
                record.ref_156_sub = stock_picking_id.origin
            else:
                record.ref_156_sub = record.ref

    @api.depends('move_id', 'debit', 'credit')
    def get_account_doi_ung_1121(self):
        for record in self:
            list = record.get_account_1121()
            if '1121' in list:
                record.account_doi_ung_1121 = True
            else:
                record.account_doi_ung_1121 = False


    def _get_product_id(self):
        for record in self:
            if record.product_id:
                record.product_default_code = record.product_id.default_code
                record.product_name = record.product_id.name

    def _get_product_price(self):
        for record in self:
            if record.quantity:
                record.product_price = (record.debit + record.credit) / record.quantity

    def get_account_1121(self):
        move_id = self.move_id
        if self.debit > self.credit:
            list = []
            for line in move_id.line_ids:
                if line.credit > 0 and line.account_id.code not in list:
                    list.append(line.account_id.code)

        elif self.debit < self.credit:
            list = []
            for line in move_id.line_ids:
                if line.debit > 0 and line.account_id.code not in list:
                    list.append(line.account_id.code)
        else:
            list = []
            for line in move_id.line_ids.filtered(lambda l: l.account_id.code != self.account_id.code):
                if line.account_id.code not in list:
                    list.append(line.account_id.code)

        return list

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        context = self._context.copy() or {}
        if context.get('context',False):
            new_context = context['context']
            if new_context.get('date_filter',False) == 'custom':
                if new_context.get('date_from', False):
                    domain.append(['date','>=',new_context['date_from']])
                if new_context.get('date_to', False):
                    domain.append(['date','<=',new_context['date_to']])
        # if 'bao_cao_1121' in context:
        #     domain_add = []
        #     account_move_line_ids = self.search(domain)
        #     for do in domain:
        #         if 'account_id.code' in do and '1121' in do:
        #             domain.remove(do)
        #             break
        #     for aml_id in account_move_line_ids:
        #         domain_add += aml_id.get_account_1121()
        #     if domain_add:
        #         domain.append(['id','in',domain_add])
        context.update({'args': domain})
        res = super(account_move_line, self.with_context(context)).search_read(domain=domain, fields=fields,
                                                                               offset=offset, limit=limit, order=order)
        return res

    def _get_name_sub(self):
        for record in self:
            if record.name == '/' and record.ref:
                if 'PO' in record.ref:
                    record.name_sub = 'Mua hàng'
                elif 'RTP' in record.ref:
                    record.name_sub = 'Trả hàng mua'
                elif 'SO' in record.ref:
                    record.name_sub = 'Bán hàng'
                elif 'RT' in record.ref:
                    record.name_sub = 'Trả hàng bán'
            else:
                record.name_sub = record.name

    def get_so_du(self):
        partner_id = False
        args = False
        account_id = []
        move_line_ids = []
        domain_not_date = []
        if self._context.get('args', False):
            args = self._context.get('args', False)
            domain_not_date = self._context.get('args', False)
        # if args and any(['partner_id' in a for a in args]):
        #     partner = [x for x in args if 'partner_id' in x]
        #     if type(partner[0][2]) is int:
        #         partner_id = [partner[0][2]]
        #     elif type(partner[0][2]) is unicode:
        #         parnter_ids = self.env['res.partner'].search([('name', 'ilike', partner[0][2])])
        #         partner_id = parnter_ids.ids
        #     else:
        #         partner_id = list(partner[0][2])
        # if args and any(['account_id.code' in a for a in args]):
        #     for domain in args:
        #         if 'account_id.code' in domain:
        #             account_list = self.env['account.account'].search([('code', domain[1], domain[2])])
        #             for account in account_list:
        #                 account_id.append(account.id)
                        # account_id.append(account_list.ids)
            # account_domain = [a for a in args if 'account_id.code' in a][0]
            # account_id  = self.env['account.account'].search([('code',account_domain[1],account_domain[2])])
            # account_id = account_id.ids
        # if args and any(['id' in a for a in args]):
        #     line_ids = [x for x in args if 'id' in x]
        #     if type(line_ids[0][2]) is list:
        #         move_line_ids = line_ids[0][2]

        if domain_not_date and any(['date' in a for a in args]):
            domain_not_date = filter(lambda rec: rec[0] != 'date', domain_not_date)
            # for index in range(len(domain_not_date)):
            #     if 'date' in domain_not_date[index]:
            #         domain_not_date.pop(index)

        # if args and any(['id' in a for a in args]):
        #     line_ids = [x for x in args if 'id' in x]
        #     if type(line_ids[0][2]) is list:
        #         move_line_ids = line_ids[0][2]

        move_ids = self.env['account.move.line'].search(args)
        before_move = self.env['account.move.line'].search(domain_not_date)
        move_line_ids = move_ids.ids

        for record in self:
            if not account_id and record.account_id and not self.env.context.get('pnl_from_sale',False):
                account_id = record.account_id.ids
            no_before, co_before = record.with_context(filter_domain_not_date=before_move.ids)._get_debit_credit_before_to_131(partner_id,account_id,move_line_ids)
            sum_amount = no_before + record.debit - co_before - record.credit
            if sum_amount > 0:
                record.so_du_no = sum_amount
                record.so_du_co = 0
            else:
                record.so_du_no = 0
                record.so_du_co = -sum_amount

    @api.model
    def _get_debit_credit_before_to_131(self, partner_id, account_id, move_line_ids):
        no_before = co_before = 0
        no_before_value = co_before_value = 0
        if self.date:
            query = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                                FROM account_move_line aml 
                                                WHERE aml.date < '%s' """ %self.date
            # if account_id:
            #     query += 'AND aml.account_id in (%s) ' % (', '.join(str(id) for id in account_id))
            # if partner_id:
            #     query += 'AND aml.partner_id in (%s) ' % (', '.join(str(id) for id in partner_id))
            # if move_line_ids and len(move_line_ids):
            #     query += 'AND id in (%s) ' % (', '.join(str(id) for id in move_line_ids))
            if self.env.context.get('filter_domain_not_date',False):
                query += 'AND id in (%s) ' % (', '.join(str(id) for id in self.env.context.get('filter_domain_not_date',False)))
            self.env.cr.execute(query)
            move_before = self.env.cr.fetchall()
            if move_before[0] and (move_before[0][0] or move_before[0][1]):
                no_before = move_before[0][0]
                co_before = move_before[0][1]
            if account_id != self.env['account.account'].search([('code','=','1111')],limit=1).ids:
                query1 = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                                                FROM account_move_line aml 
                                                                WHERE aml.date = '%s' AND aml.id < '%s' """ % (self.date, self.id)
            else:
                query1 = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                                                                FROM account_move_line aml 
                                                                                WHERE aml.date = '%s' AND aml.ref < '%s' """ % (self.date, self.ref)
            # if account_id:
            #     query1 += 'AND aml.account_id in (%s) ' % (', '.join(str(id) for id in account_id))
            # if partner_id:
            #     query1 += 'AND aml.partner_id in (%s) ' % (', '.join(str(id) for id in partner_id))
            if move_line_ids and len(move_line_ids):
                query1 += 'AND id in (%s) ' % (', '.join(str(id) for id in move_line_ids))
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

    # @api.model
    # def get_debit_credit_before(self, domain_list, start_date, partner_str):
    #     account_code = False
    #     partner_ids = False
    #     ref = product_code = move_id = False
    #
    #     account_id = account_ids = False
    #     if not domain_list:
    #         domain_list = []
    #     for domain in domain_list:
    #         if 'account_id.code' in domain:
    #             account_code = domain[2]
    #         elif 'account_doi_ung_1121' in domain:
    #             account_code = '1121'
    #         elif 'account_id' in domain:
    #             account_code = self.env['account.account'].search([('id', '=', domain[2])], limit=1).code
    #         if 'product_id' in domain:
    #             product_code = domain[2]
    #         if 'ref' in domain:
    #             ref = domain[2]
    #         if 'move_id' in domain:
    #             move_id = domain[2]
    #
    #     start_date = (datetime.strptime(start_date, "%d/%m/%Y")).strftime(
    #         DEFAULT_SERVER_DATE_FORMAT) if start_date else False
    #     if account_code:
    #         if '%' in account_code:
    #             account_ids = self.env['account.account'].search([('code', '=like', account_code)])
    #         else:
    #             account_id = self.env['account.account'].search([('code', '=', account_code)],
    #                                                             limit=1) if account_code else False
    #         no_before = co_before = 0
    #         no_before_value = co_before_value = 0
    #         if (account_id and start_date) or (account_ids and start_date):
    #             if account_id:
    #                 query = """SELECT
    #                                             SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
    #                                         FROM account_move_line aml
    #                                         WHERE aml.account_id = '%s' AND aml.date < '%s' """ % (
    #                 account_id.id, start_date)
    #             else:
    #                 query = """SELECT
    #                                                             SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
    #                                                         FROM account_move_line aml
    #                                                         WHERE aml.account_id in (%s) AND aml.date < '%s' """ % (
    #                     ', '.join(str(id) for id in account_ids.ids), start_date)
    #             if partner_str:
    #                 customer_ids = []
    #                 name_upper = partner_str.upper()
    #                 self.env.cr.execute(
    #                     "select id from res_partner where upper(name) = '%s'" % (name_upper))
    #                 res_trans = self.env.cr.fetchall()
    #                 for line in res_trans:
    #                     customer_ids.append(line[0])
    #                 if customer_ids:
    #                     query += """
    #                         AND aml.partner_id in (%s)
    #                     """ % (', '.join(str(id) for id in customer_ids))
    #                 else:
    #                     return '{0:,.2f}'.format(int(no_before_value)), '{0:,.2f}'.format(int(co_before_value))
    #             if product_code or ref or move_id:
    #                 move_ids = self.search(domain_list)
    #                 if move_ids:
    #                     product_id = move_ids.mapped('product_id')
    #                     query += """
    #                                 AND aml.id in (%s)
    #                             """ % (', '.join(str(id.id) for id in move_ids))
    #             self.env.cr.execute(query)
    #             move_before = self.env.cr.fetchall()
    #             if move_before and len(move_before) > 0:
    #                 if move_before[0][0] or move_before[0][1]:
    #                     no_before = move_before[0][0]
    #                     co_before = move_before[0][1]
    #             if (no_before - co_before) > 0:
    #                 no_before_value = no_before - co_before
    #                 co_before_value = 0
    #             else:
    #                 no_before_value = 0
    #                 co_before_value = co_before - no_before
    #         return '{0:,.2f}'.format(no_before_value), '{0:,.2f}'.format(co_before_value)

    @api.model
    def get_debit_credit_before_131(self, start_date, partner_str):
        start_date = (datetime.strptime(start_date, "%d/%m/%Y")).strftime(
            DEFAULT_SERVER_DATE_FORMAT) if start_date else False
        account_id = self.env['account.account'].search([('code', '=', 131)],
                                                        limit=1)
        no_before = co_before = 0
        no_before_value = co_before_value = 0
        if account_id and start_date:
            query = """SELECT 
                                            SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                        FROM account_move_line aml 
                                        WHERE aml.account_id = '%s' AND aml.date < '%s' """ % (
                account_id.id, start_date)
            if partner_str:
                customer_ids = []
                name_upper = partner_str.upper()
                self.env.cr.execute(
                    "select id from res_partner where upper(name) = '%s'" % (name_upper))
                res_trans = self.env.cr.fetchall()
                for line in res_trans:
                    customer_ids.append(line[0])
                if customer_ids:
                    query += """
                            AND aml.partner_id in (%s)
                        """ % (', '.join(str(id) for id in customer_ids))
                else:
                    return '{0:,.2f}'.format(no_before_value), '{0:,.2f}'.format(co_before_value)
            self.env.cr.execute(query)
            move_before = self.env.cr.fetchall()
            if move_before and len(move_before) > 0:
                if move_before[0][0] or move_before[0][1]:
                    no_before = move_before[0][0]
                    co_before = move_before[0][1]
            if (no_before - co_before) > 0:
                no_before_value = no_before - co_before
                co_before_value = 0
            else:
                no_before_value = 0
                co_before_value = co_before - no_before
        return '{0:,.2f}'.format(no_before_value), '{0:,.2f}'.format(co_before_value)

    @api.model
    def get_debit_credit_before_331(self, start_date, partner_str):
        start_date = (datetime.strptime(start_date, "%d/%m/%Y")).strftime(
            DEFAULT_SERVER_DATE_FORMAT) if start_date else False
        account_id = self.env['account.account'].search([('code', '=', 331)],
                                                        limit=1)
        no_before = co_before = 0
        no_before_value = co_before_value = 0
        if account_id and start_date:
            query = """SELECT 
                                                SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                            FROM account_move_line aml 
                                            WHERE aml.account_id = '%s' AND aml.date < '%s' """ % (
                account_id.id, start_date)
            if partner_str:
                customer_ids = []
                name_upper = partner_str.upper()
                self.env.cr.execute(
                    "select id from res_partner where upper(name) = '%s'" % (name_upper))
                res_trans = self.env.cr.fetchall()
                for line in res_trans:
                    customer_ids.append(line[0])
                if customer_ids:
                    query += """
                                AND aml.partner_id in (%s)
                            """ % (', '.join(str(id) for id in customer_ids))
                else:
                    return '{0:,.2f}'.format(no_before_value), '{0:,.2f}'.format(co_before_value)
            self.env.cr.execute(query)
            move_before = self.env.cr.fetchall()
            if move_before and len(move_before) > 0:
                if move_before[0][0] or move_before[0][1]:
                    no_before = move_before[0][0]
                    co_before = move_before[0][1]
            if (no_before - co_before) > 0:
                no_before_value = no_before - co_before
                co_before_value = 0
            else:
                no_before_value = 0
                co_before_value = co_before - no_before
        return '{0:,.2f}'.format(no_before_value), '{0:,.2f}'.format(co_before_value)

    # @api.model
    # def get_debit_credit_current(self, domain_list, start_date, end_date, partner_str):
    #     account_code = False
    #     partner_ids = False
    #     account_id = account_ids = move_id = False
    #     ref = product_code = False
    #     if not domain_list:
    #         domain_list = []
    #     for domain in domain_list:
    #         if 'account_id.code' in domain:
    #             account_code = domain[2]
    #         elif 'account_doi_ung_1121' in domain:
    #             account_code = '1121'
    #         elif 'account_id' in domain:
    #             account_code = self.env['account.account'].search([('id', '=', domain[2])],limit=1).code
    #         if 'product_id' in domain:
    #             product_code = domain[2]
    #         if 'ref' in domain:
    #             ref = domain[2]
    #         if 'move_id' in domain:
    #             ref = domain[2]
    #     if account_code:
    #         if '%' in account_code:
    #             account_ids = self.env['account.account'].search([('code', '=like', account_code)])
    #         else:
    #             account_id = self.env['account.account'].search([('code', '=', account_code)],
    #                                                             limit=1) if account_code else False
    #         no_before = co_before = 0
    #         no_before_value = co_before_value = 0
    #         no_current = co_current = 0
    #         no_value = co_value = 0
    #         if account_id:
    #             query_before = """SELECT
    #                                                         SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
    #                                                     FROM account_move_line aml
    #                                                     WHERE aml.account_id = '%s'""" % (
    #                 account_id.id)
    #
    #             query = """SELECT
    #                                             SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
    #                                         FROM account_move_line aml
    #                                         WHERE aml.account_id = '%s'""" % (
    #                 account_id.id)
    #             if start_date:
    #                 start_date = (datetime.strptime(start_date, "%d/%m/%Y")).strftime(
    #                     DEFAULT_SERVER_DATE_FORMAT)
    #                 query_before += """
    #                                                             AND aml.date < '%s'
    #                                                         """ % start_date
    #                 query += """
    #                                             AND aml.date >= '%s'
    #                                         """ % start_date
    #
    #             if end_date:
    #                 end_date = (datetime.strptime(end_date, "%d/%m/%Y")).strftime(
    #                     DEFAULT_SERVER_DATE_FORMAT)
    #                 query += """
    #                                             AND aml.date <= '%s'
    #                                         """ % end_date
    #             if partner_str:
    #                 customer_ids = []
    #                 name_upper = partner_str.upper()
    #                 self.env.cr.execute(
    #                     "select id from res_partner where upper(name) = '%s'" % (name_upper))
    #                 res_trans = self.env.cr.fetchall()
    #                 for line in res_trans:
    #                     customer_ids.append(line[0])
    #                 if customer_ids:
    #                     query_before += """
    #                                                 AND aml.partner_id in (%s)
    #                                             """ % (', '.join(str(id) for id in customer_ids))
    #                     query += """
    #                             AND aml.partner_id in (%s)
    #                         """ % (', '.join(str(id) for id in customer_ids))
    #                 else:
    #                     return '{0:,.2f}'.format(no_current), '{0:,.2f}'.format(co_current), '{0:,.2f}'.format(
    #                         no_value), '{0:,.2f}'.format(co_value)
    #
    #             if product_code or ref or move_id:
    #                 move_ids = self.search(domain_list)
    #                 if move_ids:
    #                     product_id = move_ids.mapped('product_id')
    #                     query_before += """
    #                                         AND aml.id in (%s)
    #                                     """ % (', '.join(str(id.id) for id in move_ids))
    #                     query += """
    #                                 AND aml.id in (%s)
    #                             """ % (', '.join(str(id.id) for id in move_ids))
    #
    #             if start_date:
    #                 self.env.cr.execute(query_before)
    #                 move_before = self.env.cr.fetchall()
    #                 if move_before and len(move_before) > 0:
    #                     if move_before[0][0] or move_before[0][1]:
    #                         no_before = move_before[0][0]
    #                         co_before = move_before[0][1]
    #                 if (no_before - co_before) > 0:
    #                     no_before_value = no_before - co_before
    #                     co_before_value = 0
    #                 else:
    #                     no_before_value = 0
    #                     co_before_value = co_before - no_before
    #
    #             self.env.cr.execute(query)
    #             move_current = self.env.cr.fetchall()
    #             if move_current and len(move_current) > 0:
    #                 if move_current[0][0] or move_current[0][1]:
    #                     no_current = move_current[0][0]
    #                     co_current = move_current[0][1]
    #         if account_ids:
    #             query_before = """SELECT
    #                                                                     SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
    #                                                                 FROM account_move_line aml
    #                                                                 WHERE aml.account_id in (%s)""" % (
    #                 ', '.join(str(id) for id in account_ids.ids))
    #
    #             query = """SELECT
    #                                                         SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
    #                                                     FROM account_move_line aml
    #                                                     WHERE aml.account_id in (%s)""" % (
    #                 ', '.join(str(id) for id in account_ids.ids))
    #             if start_date:
    #                 start_date = (datetime.strptime(start_date, "%d/%m/%Y")).strftime(
    #                     DEFAULT_SERVER_DATE_FORMAT)
    #                 query_before += """
    #                                                                         AND aml.date < '%s'
    #                                                                     """ % start_date
    #                 query += """
    #                                                         AND aml.date >= '%s'
    #                                                     """ % start_date
    #
    #             if end_date:
    #                 end_date = (datetime.strptime(end_date, "%d/%m/%Y")).strftime(
    #                     DEFAULT_SERVER_DATE_FORMAT)
    #                 query += """
    #                                                         AND aml.date <= '%s'
    #                                                     """ % end_date
    #             if partner_str:
    #                 customer_ids = []
    #                 name_upper = partner_str.upper()
    #                 self.env.cr.execute(
    #                     "select id from res_partner where upper(name) LIKE '%s'" % ("%" + name_upper + "%"))
    #                 res_trans = self.env.cr.fetchall()
    #                 for line in res_trans:
    #                     customer_ids.append(line[0])
    #                 if customer_ids:
    #                     query_before += """
    #                                                             AND aml.partner_id in (%s)
    #                                                         """ % (', '.join(str(id) for id in customer_ids))
    #                     query += """
    #                                         AND aml.partner_id in (%s)
    #                                     """ % (', '.join(str(id) for id in customer_ids))
    #                 else:
    #                     return '{0:,.2f}'.format(no_current), '{0:,.2f}'.format(co_current), '{0:,.2f}'.format(
    #                         no_value), '{0:,.2f}'.format(co_value)
    #             if start_date:
    #                 self.env.cr.execute(query_before)
    #                 move_before = self.env.cr.fetchall()
    #                 if move_before and len(move_before) > 0:
    #                     if move_before[0][0] or move_before[0][1]:
    #                         no_before = move_before[0][0]
    #                         co_before = move_before[0][1]
    #                 if (no_before - co_before) > 0:
    #                     no_before_value = no_before - co_before
    #                     co_before_value = 0
    #                 else:
    #                     no_before_value = 0
    #                     co_before_value = co_before - no_before
    #
    #             self.env.cr.execute(query)
    #             move_current = self.env.cr.fetchall()
    #             if move_current and len(move_current) > 0:
    #                 if move_current[0][0] or move_current[0][1]:
    #                     no_current = move_current[0][0]
    #                     co_current = move_current[0][1]
    #         temp = no_before_value + no_current - co_current - co_before_value
    #         if temp > 0:
    #             no_value = temp
    #             co_value = 0
    #         else:
    #             no_value = 0
    #             co_value = - temp
    #         return '{0:,.2f}'.format(no_current), '{0:,.2f}'.format(co_current), '{0:,.2f}'.format(
    #             no_value), '{0:,.2f}'.format(co_value)

    @api.model
    def get_debit_credit_current_131(self, domain_list, start_date, end_date, partner_str):
        account_id = self.env['account.account'].search([('code', '=', 131)],
                                                        limit=1)
        no_before = co_before = 0
        no_before_value = co_before_value = 0
        no_current = co_current = 0
        no_value = co_value = 0
        if account_id:
            query_before = """SELECT 
                                                            SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                                        FROM account_move_line aml 
                                                        WHERE aml.account_id = '%s'""" % (
                account_id.id)

            query = """SELECT 
                                                SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                            FROM account_move_line aml 
                                            WHERE aml.account_id = '%s'""" % (
                account_id.id)
            if start_date:
                start_date = (datetime.strptime(start_date, "%d/%m/%Y")).strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
                query_before += """
                                                                AND aml.date < '%s'
                                                            """ % start_date
                query += """
                                                AND aml.date >= '%s'
                                            """ % start_date

            if end_date:
                end_date = (datetime.strptime(end_date, "%d/%m/%Y")).strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
                query += """
                                                AND aml.date <= '%s'
                                            """ % end_date
            if partner_str:
                customer_ids = []
                name_upper = partner_str.upper()
                self.env.cr.execute(
                    "select id from res_partner where upper(name) = '%s'" % (name_upper))
                res_trans = self.env.cr.fetchall()
                for line in res_trans:
                    customer_ids.append(line[0])
                if customer_ids:
                    query_before += """
                                                    AND aml.partner_id in (%s)
                                                """ % (', '.join(str(id) for id in customer_ids))
                    query += """
                                AND aml.partner_id in (%s)
                            """ % (', '.join(str(id) for id in customer_ids))
                else:
                    return '{0:,.2f}'.format(no_current), '{0:,.2f}'.format(co_current), '{0:,.2f}'.format(
                        no_value), '{0:,.2f}'.format(co_value)
            if start_date:
                self.env.cr.execute(query_before)
                move_before = self.env.cr.fetchall()
                if move_before and len(move_before) > 0:
                    if move_before[0][0] or move_before[0][1]:
                        no_before = move_before[0][0]
                        co_before = move_before[0][1]
                if (no_before - co_before) > 0:
                    no_before_value = no_before - co_before
                    co_before_value = 0
                else:
                    no_before_value = 0
                    co_before_value = co_before - no_before

            self.env.cr.execute(query)
            move_current = self.env.cr.fetchall()
            if move_current and len(move_current) > 0:
                if move_current[0][0] or move_current[0][1]:
                    no_current = move_current[0][0]
                    co_current = move_current[0][1]
        temp = no_before_value + no_current - co_current - co_before_value
        if temp > 0:
            no_value = temp
            co_value = 0
        else:
            no_value = 0
            co_value = - temp
        return '{0:,.2f}'.format(no_current), '{0:,.2f}'.format(co_current), '{0:,.2f}'.format(
            no_value), '{0:,.2f}'.format(co_value)

    @api.model
    def get_debit_credit_current_331(self, domain_list, start_date, end_date, partner_str):
        account_id = self.env['account.account'].search([('code', '=', 331)],
                                                        limit=1)
        no_before = co_before = 0
        no_before_value = co_before_value = 0
        no_current = co_current = 0
        no_value = co_value = 0
        if account_id:
            query_before = """SELECT 
                                                                SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                                            FROM account_move_line aml 
                                                            WHERE aml.account_id = '%s'""" % (
                account_id.id)

            query = """SELECT 
                                                    SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                                FROM account_move_line aml 
                                                WHERE aml.account_id = '%s'""" % (
                account_id.id)
            if start_date:
                start_date = (datetime.strptime(start_date, "%d/%m/%Y")).strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
                query_before += """
                                                                    AND aml.date < '%s'
                                                                """ % start_date
                query += """
                                                    AND aml.date >= '%s'
                                                """ % start_date

            if end_date:
                end_date = (datetime.strptime(end_date, "%d/%m/%Y")).strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
                query += """
                                                    AND aml.date <= '%s'
                                                """ % end_date
            if partner_str:
                customer_ids = []
                name_upper = partner_str.upper()
                self.env.cr.execute(
                    "select id from res_partner where upper(name) = '%s'" % (name_upper))
                res_trans = self.env.cr.fetchall()
                for line in res_trans:
                    customer_ids.append(line[0])
                if customer_ids:
                    query_before += """
                                                        AND aml.partner_id in (%s)
                                                    """ % (', '.join(str(id) for id in customer_ids))
                    query += """
                                    AND aml.partner_id in (%s)
                                """ % (', '.join(str(id) for id in customer_ids))
                else:
                    return '{0:,.2f}'.format(no_current), '{0:,.2f}'.format(co_current), '{0:,.2f}'.format(
                        no_value), '{0:,.2f}'.format(co_value)
            if start_date:
                self.env.cr.execute(query_before)
                move_before = self.env.cr.fetchall()
                if move_before and len(move_before) > 0:
                    if move_before[0][0] or move_before[0][1]:
                        no_before = move_before[0][0]
                        co_before = move_before[0][1]
                if (no_before - co_before) > 0:
                    no_before_value = no_before - co_before
                    co_before_value = 0
                else:
                    no_before_value = 0
                    co_before_value = co_before - no_before

            self.env.cr.execute(query)
            move_current = self.env.cr.fetchall()
            if move_current and len(move_current) > 0:
                if move_current[0][0] or move_current[0][1]:
                    no_current = move_current[0][0]
                    co_current = move_current[0][1]
        temp = no_before_value + no_current - co_current - co_before_value
        if temp > 0:
            no_value = temp
            co_value = 0
        else:
            no_value = 0
            co_value = - temp
        return '{0:,.2f}'.format(no_current), '{0:,.2f}'.format(co_current), '{0:,.2f}'.format(
            no_value), '{0:,.2f}'.format(co_value)

    # def get_account_xlsx(self, data, response):
    #     output = StringIO.StringIO()
    #     workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    #     worksheet = workbook.add_worksheet('Sheet1')
    #
    #     account_ids = account_id = False
    #     if '%' in data['code']:
    #         account_ids = self.env['account.account'].search([('code', '=like', data['code'])])
    #         conditions = [('account_id', 'in', account_ids.ids)]
    #     else:
    #         account_id = self.env['account.account'].search([('code', '=', data['code'])], limit=1)
    #         conditions = [('account_id', '=', account_id.id)]
    #     start_date = data['start_date']
    #     end_date = data['end_date']
    #     partner = data['partner_str']
    #     partner_ids = []
    #     no_before = co_before = 0
    #     if data['partner_str']:
    #         customer_ids = []
    #         name_upper = data['partner_str'].upper()
    #         self.env.cr.execute("select id from res_partner where upper(name) = '%s'" % (name_upper))
    #         res_trans = self.env.cr.fetchall()
    #         if len(res_trans) > 0:
    #             customer_ids.append(res_trans[0][0])
    #             partner_ids = customer_ids
    #     #     else:
    #     #         self.env.cr.execute("select id from res_partner where upper(name) LIKE '%s'" % ("%" + name_upper + "%"))
    #     #         res_trans = self.env.cr.fetchall()
    #     #         for line in res_trans:
    #     #             customer_ids.append(line[0])
    #     #         if customer_ids:
    #     #             partner_ids = customer_ids
    #     #         else:
    #     #             partner = False
    #     # if partner == False:
    #     #     True
    #
    #     no_before_value = co_before_value = no_before = co_before = 0
    #     if start_date:
    #         start_date = (datetime.strptime(start_date, "%d/%m/%Y")).strftime(DEFAULT_SERVER_DATE_FORMAT)
    #         conditions.append(('date', '>=', start_date))
    #         if account_ids:
    #             query = """SELECT
    #                                                                     SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
    #                                                                 FROM account_move_line aml
    #                                                                 WHERE aml.account_id in (%s) AND aml.date < '%s' """ % (
    #                 ', '.join(str(id) for id in account_ids.ids), start_date)
    #         else:
    #             query = """SELECT
    #                                                     SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
    #                                                 FROM account_move_line aml
    #                                                 WHERE aml.account_id = '%s' AND aml.date < '%s' """ % (
    #                 account_id.id, start_date)
    #         if data['partner_str']:
    #             customer_ids = []
    #             name_upper = data['partner_str'].upper()
    #             self.env.cr.execute(
    #                 "select id from res_partner where upper(name) LIKE '%s'" % ("%" + name_upper + "%"))
    #             res_trans = self.env.cr.fetchall()
    #             for line in res_trans:
    #                 customer_ids.append(line[0])
    #             if customer_ids:
    #                 query += """
    #                                 AND aml.partner_id in (%s)
    #                             """ % (', '.join(str(id) for id in customer_ids))
    #         self.env.cr.execute(query)
    #         move_before = self.env.cr.fetchall()
    #         if move_before and len(move_before) > 0:
    #             if move_before[0][0] or move_before[0][1]:
    #                 no_before = move_before[0][0]
    #                 co_before = move_before[0][1]
    #         if (no_before - co_before) > 0:
    #             no_before_value = no_before - co_before
    #             co_before_value = 0
    #         else:
    #             no_before_value = 0
    #             co_before_value = co_before - no_before
    #         if partner == False:
    #             co_before_value = no_before_value = 0
    #
    #             # month = (datetime.strptime(start_date, "%d/%m/%Y")).month
    #             # year = (datetime.strptime(start_date, "%d/%m/%Y")).year
    #             # start_date = (datetime.strptime(start_date, "%d/%m/%Y")).strftime(DEFAULT_SERVER_DATE_FORMAT)
    #             # conditions.append(('date', '>=', start_date))
    #             # conditions_before.append(('date', '<', start_date))
    #             # if partner_ids:
    #             #     conditions_before.append(('partner_id', 'in', partner_ids))
    #             # data_before = self.search(conditions_before, order='date asc, ref asc')
    #             # for data_line in data_before:
    #             #     no_before += data_line.debit
    #             #     co_before += data_line.credit
    #     if end_date:
    #         end_date = (datetime.strptime(end_date, "%d/%m/%Y")).strftime(DEFAULT_SERVER_DATE_FORMAT)
    #         conditions.append(('date', '<=', end_date))
    #     if partner_ids:
    #         conditions.append(('partner_id', 'in', partner_ids))
    #
    #     header_body_color = workbook.add_format({
    #         'bold': True,
    #         'font_size': '11',
    #         'align': 'center',
    #         'valign': 'vcenter',
    #     })
    #     header_bold_color = workbook.add_format({
    #         'bold': True,
    #         'font_size': '11',
    #         'align': 'left',
    #         'valign': 'vcenter',
    #         'bg_color': 'cce0ff',
    #         'border': 1,
    #     })
    #     body_bold_table = workbook.add_format(
    #         {'bold': False, 'border': 1, 'font_size': '12', 'align': 'left', 'valign': 'vcenter'})
    #     title_report = workbook.add_format(
    #         {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
    #     money = workbook.add_format({
    #         'num_format': '#,##0',
    #         'border': 1,
    #     })
    #
    #     if data['code'] in ('1561','632'):
    #         back_color = 'A1:G1'
    #
    #         worksheet.set_column('A:A', 15)
    #         worksheet.set_column('B:B', 15)
    #         worksheet.set_column('C:C', 15)
    #         worksheet.set_column('D:D', 30)
    #         worksheet.set_column('E:E', 15)
    #         worksheet.set_column('F:F', 60)
    #         worksheet.set_column('G:N', 15)
    #
    #         worksheet.merge_range('A1:G1', ("SỔ CHI TIẾT CÁC TÀI KHOẢN %s" % (account_id.code)),
    #                               title_report) if account_id else worksheet.merge_range('A1:G1', (
    #             "SỔ CHI TIẾT CÁC TÀI KHOẢN %s" % (data['code'].split('%')[0])), title_report)
    #         worksheet.merge_range('A2:G2', (
    #             "Tài khoản: %s;" % (data['code'])),
    #                               header_body_color)
    #
    #         header = [
    #             'Ngày hạch toán',
    #             'Ngày chứng từ',
    #             'Số chứng từ',
    #             'Đối tác',
    #             'Mã sản phẩm',
    #             'Tên sản phẩm',
    #             'Đơn giá',
    #             'SL',
    #             'Tài khoản',
    #             'TK đối ứng',
    #             'Phát sinh Nợ',
    #             'Phát sinh Có',
    #             'Dư Nợ',
    #             'Dư Có'
    #         ]
    #         row = 3
    #
    #         [worksheet.write(row, header_cell, (header[header_cell]), header_bold_color) for
    #          header_cell in
    #          range(0, len(header)) if header[header_cell]]
    #         no_before_amount = co_before_amount = 0
    #         if (no_before - co_before) > 0:
    #             no_before_amount = no_before - co_before
    #             co_before_amount = 0
    #         elif (co_before - no_before) > 0:
    #             co_before_amount = co_before - no_before
    #             no_before_amount = 0
    #         row += 1
    #         worksheet.write(row, 10, ("Số dư đầu kỳ"), body_bold_table)
    #         worksheet.write(row, 11, account_id.code, body_bold_table) if account_id else worksheet.write(row, 4,
    #                                                                                                      data[
    #                                                                                                          'code'].split(
    #                                                                                                          '%')[0],
    #                                                                                                      body_bold_table)
    #         worksheet.write(row, 12, no_before_amount, money)
    #         worksheet.write(row, 13, co_before_amount, money)
    #
    #         no_current = 0.0
    #         co_current = 0.0
    #         data_line_report = []
    #         current_data = self.search(conditions, order='date asc, ref asc')  # , order='partner_id asc, date asc'
    #         if partner == False:
    #             current_data = []
    #         for data_line in current_data:
    #             no_current += data_line.debit
    #             co_current += data_line.credit
    #             doiung = ''
    #             move_id = data_line.move_id
    #             if data_line.debit > data_line.credit:
    #                 list = []
    #                 for line in move_id.line_ids:
    #                     if line.credit > 0 and line.account_id.code not in list:
    #                         list.append(line.account_id.code)
    #                 doiung = ', '.join(list)
    #
    #             elif data_line.debit < data_line.credit:
    #                 list = []
    #                 for line in move_id.line_ids:
    #                     if line.debit > 0 and line.account_id.code not in list:
    #                         list.append(line.account_id.code)
    #                 doiung = ', '.join(list)
    #             else:
    #                 list = []
    #                 for line in move_id.line_ids.filtered(lambda l: l.account_id.code != data_line.account_id.code):
    #                     if line.account_id.code not in list:
    #                         list.append(line.account_id.code)
    #                 doiung = ', '.join(list)
    #
    #             row += 1
    #
    #             line_name = data_line.name
    #             if line_name == '/':
    #                 if data_line.ref:
    #                     if 'SO' in data_line.ref:
    #                         line_name = 'Bán hàng'
    #                     elif 'PO' in data_line.ref:
    #                         line_name = 'Mua hàng'
    #                     elif 'RTP' in data_line.ref:
    #                         line_name = 'Trả hàng mua'
    #                     elif 'RT0' in data_line.ref:
    #                         line_name = 'Trả hàng bán'
    #                 else:
    #                     if data_line.account_id.code == '331':
    #                         line_name = 'Bán hàng'
    #             temp = no_before_amount - co_before_amount + data_line.debit - data_line.credit
    #             if temp > 0:
    #                 no_before_amount = temp
    #             else:
    #                 co_before_amount = - temp
    #             worksheet.write(row, 0, data_line.date, body_bold_table)
    #             worksheet.write(row, 1, data_line.date, body_bold_table)
    #             worksheet.write(row, 2, data_line.ref or '', body_bold_table)
    #             worksheet.write(row, 3, data_line.partner_id and data_line.partner_id.name or '', body_bold_table)
    #             worksheet.write(row, 4, data_line.product_id.default_code, body_bold_table)
    #             worksheet.write(row, 5, data_line.product_id.name, body_bold_table)
    #             worksheet.write(row, 6, data_line.product_price, body_bold_table)
    #             worksheet.write(row, 7, data_line.quantity, body_bold_table)
    #             worksheet.write(row, 8, data_line.account_id.code, body_bold_table)
    #             worksheet.write(row, 9, doiung, body_bold_table)
    #             worksheet.write(row, 10, data_line.debit, money)
    #             worksheet.write(row, 11, data_line.credit, money)
    #             worksheet.write(row, 12, no_before_amount, money)
    #             worksheet.write(row, 13, co_before_amount, money)
    #
    #         row += 1
    #         worksheet.write(row, 7, ("Cộng"), body_bold_table)
    #         worksheet.write(row, 8, account_id.code, body_bold_table) if account_id else worksheet.write(row, 4,
    #                                                                                                      data[
    #                                                                                                          'code'].split(
    #                                                                                                          '%')[0],
    #                                                                                                      body_bold_table)
    #         worksheet.write(row, 9, "", body_bold_table)
    #         worksheet.write(row, 10, no_current, money)
    #         worksheet.write(row, 11, co_current, money)
    #         worksheet.write(row, 12, "", body_bold_table)
    #         worksheet.write(row, 13, "", body_bold_table)
    #
    #         no_end = 0.0
    #         co_end = 0.0
    #         sum_cong_no = no_before + no_current - co_before - co_current
    #         if sum_cong_no < 0:
    #             co_end = - sum_cong_no
    #         else:
    #             no_end = sum_cong_no
    #
    #         row += 1
    #         worksheet.write(row, 4, ("Số dư cuối kỳ"), body_bold_table)
    #         worksheet.write(row, 5, account_id.code, body_bold_table) if account_id else worksheet.write(row, 4,
    #                                                                                                      data['code'],
    #                                                                                                      body_bold_table)
    #         worksheet.write(row, 6, "", body_bold_table)
    #         worksheet.write(row, 7, "", body_bold_table)
    #         worksheet.write(row, 8, "", body_bold_table)
    #         worksheet.write(row, 9, no_end, money)
    #         worksheet.write(row, 10, co_end, money)
    #     else:
    #         back_color = 'A1:G1'
    #
    #         worksheet.set_column('A:A', 15)
    #         worksheet.set_column('B:B', 15)
    #         worksheet.set_column('C:C', 15)
    #         worksheet.set_column('D:D', 30)
    #         worksheet.set_column('E:E', 60)
    #         worksheet.set_column('F:F', 15)
    #         worksheet.set_column('G:G', 15)
    #         worksheet.set_column('H:H', 15)
    #         worksheet.set_column('I:I', 15)
    #         worksheet.set_column('J:J', 15)
    #         worksheet.set_column('K:K', 15)
    #         worksheet.set_column('H:H', 15)
    #
    #         worksheet.merge_range('A1:G1', ("SỔ CHI TIẾT CÁC TÀI KHOẢN %s" % (account_id.code)),
    #                               title_report) if account_id else worksheet.merge_range('A1:G1', (
    #             "SỔ CHI TIẾT CÁC TÀI KHOẢN %s" % (data['code'].split('%')[0])), title_report)
    #         worksheet.merge_range('A2:G2', (
    #             "Tài khoản: %s;" % (data['code'])),
    #                               header_body_color)
    #
    #         header = [
    #             'Ngày hạch toán',
    #             'Ngày chứng từ',
    #             'Số chứng từ',
    #             'Đối tác',
    #             'Diễn giải',
    #             'Tài khoản',
    #             'TK đối ứng',
    #             'Phát sinh Nợ',
    #             'Phát sinh Có',
    #             'Dư Nợ',
    #             'Dư Có'
    #         ]
    #         row = 3
    #
    #         [worksheet.write(row, header_cell, (header[header_cell]), header_bold_color) for
    #          header_cell in
    #          range(0, len(header)) if header[header_cell]]
    #         no_before_amount = co_before_amount = 0
    #         if (no_before - co_before) > 0:
    #             no_before_amount = no_before - co_before
    #             co_before_amount = 0
    #         elif (co_before - no_before) > 0:
    #             co_before_amount = co_before - no_before
    #             no_before_amount = 0
    #         row += 1
    #         worksheet.write(row, 4, ("Số dư đầu kỳ"), body_bold_table)
    #         worksheet.write(row, 5, account_id.code, body_bold_table) if account_id else worksheet.write(row, 4,
    #                                                                                                      data['code'].split(
    #                                                                                                          '%')[0],
    #                                                                                                      body_bold_table)
    #         worksheet.write(row, 9, no_before_amount, money)
    #         worksheet.write(row, 10, co_before_amount, money)
    #
    #         no_current = 0.0
    #         co_current = 0.0
    #         data_line_report = []
    #         current_data = self.search(conditions, order='date asc, ref asc')  # , order='partner_id asc, date asc'
    #         if partner == False:
    #             current_data = []
    #         for data_line in current_data:
    #             no_current += data_line.debit
    #             co_current += data_line.credit
    #             doiung = ''
    #             move_id = data_line.move_id
    #             if data_line.debit > data_line.credit:
    #                 list = []
    #                 for line in move_id.line_ids:
    #                     if line.credit > 0 and line.account_id.code not in list:
    #                         list.append(line.account_id.code)
    #                 doiung = ', '.join(list)
    #
    #             elif data_line.debit < data_line.credit:
    #                 list = []
    #                 for line in move_id.line_ids:
    #                     if line.debit > 0 and line.account_id.code not in list:
    #                         list.append(line.account_id.code)
    #                 doiung = ', '.join(list)
    #             else:
    #                 list = []
    #                 for line in move_id.line_ids.filtered(lambda l: l.account_id.code != data_line.account_id.code):
    #                     if line.account_id.code not in list:
    #                         list.append(line.account_id.code)
    #                 doiung = ', '.join(list)
    #
    #             row += 1
    #
    #             line_name = data_line.name
    #             if line_name == '/':
    #                 if data_line.ref:
    #                     if 'SO' in data_line.ref:
    #                         line_name = 'Bán hàng'
    #                     elif 'PO' in data_line.ref:
    #                         line_name = 'Mua hàng'
    #                     elif 'RTP' in data_line.ref:
    #                         line_name = 'Trả hàng mua'
    #                     elif 'RT0' in data_line.ref:
    #                         line_name = 'Trả hàng bán'
    #                 else:
    #                     if data_line.account_id.code == '331':
    #                         line_name = 'Bán hàng'
    #             temp = no_before_amount - co_before_amount + data_line.debit - data_line.credit
    #             if temp > 0:
    #                 no_before_amount = temp
    #             else:
    #                 co_before_amount = - temp
    #             worksheet.write(row, 0, data_line.date, body_bold_table)
    #             worksheet.write(row, 1, data_line.date, body_bold_table)
    #             worksheet.write(row, 2, data_line.ref or '', body_bold_table)
    #             worksheet.write(row, 3, data_line.partner_id and data_line.partner_id.name or '', body_bold_table)
    #             worksheet.write(row, 4, line_name, body_bold_table)
    #             worksheet.write(row, 5, data_line.account_id.code, body_bold_table)
    #             worksheet.write(row, 6, doiung, body_bold_table)
    #             worksheet.write(row, 7, data_line.debit, money)
    #             worksheet.write(row, 8, data_line.credit, money)
    #             worksheet.write(row, 9, no_before_amount, money)
    #             worksheet.write(row, 10, co_before_amount, money)
    #
    #         row += 1
    #         worksheet.write(row, 4, ("Cộng"), body_bold_table)
    #         worksheet.write(row, 5, account_id.code, body_bold_table) if account_id else worksheet.write(row, 4,
    #                                                                                                      data['code'].split(
    #                                                                                                          '%')[0],
    #                                                                                                      body_bold_table)
    #         worksheet.write(row, 6, "", body_bold_table)
    #         worksheet.write(row, 7, no_current, money)
    #         worksheet.write(row, 8, co_current, money)
    #         worksheet.write(row, 9, "", body_bold_table)
    #         worksheet.write(row, 10, "", body_bold_table)
    #
    #         no_end = 0.0
    #         co_end = 0.0
    #         sum_cong_no = no_before + no_current - co_before - co_current
    #         if sum_cong_no < 0:
    #             co_end = - sum_cong_no
    #         else:
    #             no_end = sum_cong_no
    #
    #         row += 1
    #         worksheet.write(row, 4, ("Số dư cuối kỳ"), body_bold_table)
    #         worksheet.write(row, 5, account_id.code, body_bold_table) if account_id else worksheet.write(row, 4, data['code'], body_bold_table)
    #         worksheet.write(row, 6, "", body_bold_table)
    #         worksheet.write(row, 7, "", body_bold_table)
    #         worksheet.write(row, 8, "", body_bold_table)
    #         worksheet.write(row, 9, no_end, money)
    #         worksheet.write(row, 10, co_end, money)
    #
    #     workbook.close()
    #     output.seek(0)
    #     response.stream.write(output.read())
    #     output.close()

    def get_account_detail_xlsx(self, data, response):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        conditions = [('account_id', '=', self.account_id.id)]
        start_date = data['start_date']
        end_date = data['end_date']
        partner_str = data['partner_str']
        partner_id = False
        no_before = co_before = 0
        if data['partner_str']:
            customer_ids = []
            name_upper = data['partner_str'].upper()
            self.env.cr.execute("select id from res_partner where upper(name) = '%s'" % (name_upper))
            res_trans = self.env.cr.fetchall()
            if len(res_trans) > 0:
                customer_ids.append(res_trans[0][0])
                partner_id = self.env['res.partner'].browse(customer_ids[0])
            # else:
            #     self.env.cr.execute(
            #         "select id from res_partner where upper(name) LIKE '%s'" % ("%" + name_upper + "%"))
            #     res_trans = self.env.cr.fetchall()
            #     for line in res_trans:
            #         customer_ids.append(line[0])
            #     if customer_ids:
            #         partner_id = self.env['res.partner'].browse(customer_ids[0])
            #     else:
            #         partner_str = False

        if partner_id and partner_id.id:
            sheet_name = '%s - %s' % (1, self.no_accent_vietnamese(partner_id.name, True))
            worksheet = workbook.add_worksheet(sheet_name)
            data_report = self.get_data_report(data, partner_id)
            data_report['order_lines'] = self.get_order_data(data, partner_id)
            self.write_data_to_sheet(workbook, worksheet, data, data_report)
        else:
            worksheet = workbook.add_worksheet('Báo cáo tổng hợp')
            data_report = self.get_data_report(data, partner_id or False)
            self.write_data_to_sheet(workbook, worksheet, data, data_report)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def write_data_to_sheet(self, workbook, worksheet, data_report, data, show_header=True, start_line=0):
        start_date = end_date = ''
        if data_report['start_date']:
            start_date = (datetime.strptime(data_report['start_date'], "%d/%m/%Y")).strftime(DEFAULT_SERVER_DATE_FORMAT)

        if data_report['end_date']:
            end_date = (datetime.strptime(data_report['end_date'], "%d/%m/%Y")).strftime(DEFAULT_SERVER_DATE_FORMAT)

        border_format = workbook.add_format({
            'border': 1
        })
        header_bold_color = workbook.add_format({
            'bold': True,
            'font_size': '14',
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': 'dddddd',
        })
        header_border_format = workbook.add_format({
            'border': 1,
            'bg_color': 'dddddd',
        })
        body_bold_color = workbook.add_format({
            'bold': False,
            'font_size': '14',
            'align': 'left',
            'valign': 'vcenter'
        })
        header_money = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
            'bg_color': 'dddddd',
        })
        money = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
        })
        number_format = workbook.add_format({
            'border': 1,
        })

        if show_header:
            header_label = "Báo cáo: %s" % (data['account'],)
            worksheet.merge_range('A1:I1', header_label.upper(), header_bold_color)

            worksheet.merge_range('A2:G2', "Kỳ báo cáo: ", body_bold_color)
            worksheet.write(start_line + 1, 7, "%s" % (start_date,), body_bold_color)
            worksheet.write(start_line + 1, 8, "%s" % (end_date or '',), body_bold_color)

            worksheet.merge_range('A3:G3', "Đối tác: ", body_bold_color)
            worksheet.write(start_line + 2, 7, "%s" % (data['name'],), body_bold_color)
            worksheet.write(start_line + 2, 8, '', body_bold_color)

            worksheet.merge_range('A4:G4', "Tài Khoản: %s" % (data['account'],), border_format)
            worksheet.write(start_line + 3, 7, "Nợ", border_format)
            worksheet.write(start_line + 3, 8, "Có", border_format)

            worksheet.set_column('A:A', 12)
            worksheet.set_column('B:B', 20)
            worksheet.set_column('C:C', 25)
            worksheet.set_column('D:D', 25)
            worksheet.set_column('E:E', 12)
            worksheet.set_column('F:F', 25)
            worksheet.set_column('G:G', 20)
            worksheet.set_column('H:H', 20)
            worksheet.set_column('I:I', 20)
            worksheet.set_column('J:J', 20)
            worksheet.set_column('K:K', 20)

            start_line += 4

        worksheet.merge_range('A%s:G%s' % (start_line + 1, start_line + 1), "Số dư đầu kỳ:", border_format)
        temp = data['no_before'] - data['co_before']
        temp_co_before = temp_no_before = 0
        if temp > 0:
            temp_no_before = temp
        else:
            temp_co_before = - temp
        worksheet.write(start_line, 7, temp_no_before, money)
        worksheet.write(start_line, 8, temp_co_before, money)

        worksheet.merge_range('A%s:G%s' % (start_line + 2, start_line + 2), "Tổng phát sinh trong kỳ:", border_format)
        worksheet.write(start_line + 1, 7, data['no_current'], money)
        worksheet.write(start_line + 1, 8, data['co_current'], money)

        worksheet.merge_range('A%s:G%s' % (start_line + 3, start_line + 3), "Số dư cuối kỳ:", border_format)
        worksheet.write(start_line + 2, 7, data['no_end'], money)
        worksheet.write(start_line + 2, 8, data['co_end'], money)

        cong_no_label = 'CÔNG NỢ TỔNG HỢP'
        worksheet.merge_range(start_line + 4, 0, start_line + 4, 8, cong_no_label, header_bold_color)
        worksheet.merge_range('A%s:A%s' % (start_line + 6, start_line + 7), "Ngày hạch toán", header_border_format)
        worksheet.merge_range('B%s:B%s' % (start_line + 6, start_line + 7), "Ngày chứng từ", header_border_format)
        worksheet.merge_range('C%s:C%s' % (start_line + 6, start_line + 7), "Số chứng từ", header_border_format)
        worksheet.merge_range('D%s:D%s' % (start_line + 6, start_line + 7), "Diễn giải", header_border_format)
        worksheet.merge_range('E%s:E%s' % (start_line + 6, start_line + 7), "TK công nợ", header_border_format)
        worksheet.merge_range('F%s:G%s' % (start_line + 6, start_line + 6), "Phát sinh", header_border_format)
        worksheet.merge_range('H%s:I%s' % (start_line + 6, start_line + 6), "Số dư	", header_border_format)
        worksheet.write(start_line + 6, 5, "Nợ", header_border_format)
        worksheet.write(start_line + 6, 6, "Có", header_border_format)
        worksheet.write(start_line + 6, 7, "Nợ", header_border_format)
        worksheet.write(start_line + 6, 8, "Có", header_border_format)

        worksheet.write(start_line + 7, 3, 'Số dư đầu kỳ', border_format)
        worksheet.write(start_line + 7, 4, data['account_code'], border_format)
        worksheet.write(start_line + 7, 5, 0, money)
        worksheet.write(start_line + 7, 6, 0, money)
        worksheet.write(start_line + 7, 7, temp_no_before, money)
        worksheet.write(start_line + 7, 8, temp_co_before, money)

        no_before = temp_no_before
        co_before = temp_co_before
        row = start_line + 8
        count = 0
        for line in data['cong_no_report']:
            #     no    += 1
            count += 1
            if no_before > 0:
                no_before += (line['debit'] - line['credit'])
                if no_before < 0:
                    co_before -= no_before
                    no_before = 0
            elif co_before > 0:
                co_before += (line['credit'] - line['debit'])
                if co_before < 0:
                    no_before -= co_before
                    co_before = 0
            else:
                no_before += (line['debit'] - line['credit'])
                if no_before < 0:
                    co_before -= no_before
                    no_before = 0
            line_name = line['name']
            if line_name == '/':
                if line['ref'].find('SO') != -1:
                    line_name = 'Bán hàng'
                elif line['ref'].find('RT0') != -1:
                    line_name = 'Trả hàng'
                elif line['ref'].find('PO') != -1:
                    line_name = 'Mua hàng'
                elif line['ref'].find('RTP') != -1:
                    line_name = 'Trả hàng mua'

            if line['credit']:
                worksheet.write(row, 0, line['date'], header_border_format)
                worksheet.write(row, 1, line['date'], header_border_format)
                worksheet.write(row, 2, line['ref'], header_border_format)
                worksheet.write(row, 3, line_name, header_border_format)
                worksheet.write(row, 4, data['account_code'] or '', header_border_format)
                worksheet.write(row, 5, line['debit'], header_money)
                worksheet.write(row, 6, line['credit'], header_money)
                worksheet.write(row, 7, no_before, header_money)
                worksheet.write(row, 8, co_before, header_money)
            else:
                worksheet.write(row, 0, line['date'], border_format)
                worksheet.write(row, 1, line['date'], border_format)
                worksheet.write(row, 2, line['ref'], border_format)
                worksheet.write(row, 3, line_name, border_format)
                worksheet.write(row, 4, data['account_code'] or '', border_format)
                worksheet.write(row, 5, line['debit'], money)
                worksheet.write(row, 6, line['credit'], money)
                worksheet.write(row, 7, no_before, money)
                worksheet.write(row, 8, co_before, money)
            row += 1

        start_line = row + 1

        sale_label = 'CÔNG NỢ CHI TIẾT'
        worksheet.merge_range(start_line, 0, start_line, 10, sale_label, header_bold_color)
        start_line += 1

        if show_header:
            worksheet.merge_range('A%s:A%s' % (start_line + 1, start_line + 2), "Ngày hạch toán", header_border_format)
            worksheet.merge_range('B%s:B%s' % (start_line + 1, start_line + 2), "Ngày chứng từ", header_border_format)
            worksheet.merge_range('C%s:C%s' % (start_line + 1, start_line + 2), "Số chứng từ", header_border_format)
            worksheet.merge_range('D%s:D%s' % (start_line + 1, start_line + 2), "Diễn giải", header_border_format)
            worksheet.merge_range('E%s:E%s' % (start_line + 1, start_line + 2), "Mã hàng", header_border_format)
            worksheet.merge_range('F%s:F%s' % (start_line + 1, start_line + 2), "TK công nợ", header_border_format)
            worksheet.merge_range('G%s:G%s' % (start_line + 1, start_line + 2), "TK đối ứng", header_border_format)
            worksheet.merge_range('H%s:I%s' % (start_line + 1, start_line + 1), "Phát sinh", header_border_format)
            worksheet.merge_range('J%s:K%s' % (start_line + 1, start_line + 1), "Số dư	", header_border_format)
            worksheet.write(start_line + 1, 7, "Nợ", header_border_format)
            worksheet.write(start_line + 1, 8, "Có", header_border_format)
            worksheet.write(start_line + 1, 9, "Nợ", header_border_format)
            worksheet.write(start_line + 1, 10, "Có", header_border_format)

            start_line += 2

        worksheet.write(start_line, 0, 'Đối tác: %s' % (data['name'],), border_format)
        worksheet.write(start_line, 7, data['no_current'], money)
        worksheet.write(start_line, 8, data['co_current'], money)
        start_line += 1

        worksheet.write(start_line, 3, 'Số dư đầu kỳ', border_format)
        worksheet.write(start_line, 4, '', border_format)
        worksheet.write(start_line, 5, data['account_code'], border_format)
        worksheet.write(start_line, 6, '', border_format)
        worksheet.write(start_line, 7, 0, money)
        worksheet.write(start_line, 8, 0, money)
        worksheet.write(start_line, 9, temp_no_before, money)
        worksheet.write(start_line, 10, temp_co_before, money)
        start_line += 1

        vat_lines = []

        row = start_line
        # no_before = data['no_before']
        # co_before = data['co_before']
        no_before = temp_no_before
        co_before = temp_co_before
        count = 0
        # no    = 0
        for line in data['data_line_report']:
            #     no    += 1
            count += 1
            if no_before > 0:
                no_before += (line['debit'] - line['credit'])
                if no_before < 0:
                    co_before -= no_before
                    no_before = 0
            elif co_before > 0:
                co_before += (line['credit'] - line['debit'])
                if co_before < 0:
                    no_before -= co_before
                    co_before = 0
            else:
                no_before += (line['debit'] - line['credit'])
                if no_before < 0:
                    co_before -= no_before
                    no_before = 0
            if line['credit']:
                worksheet.write(row, 0, line['date'], header_border_format)
                worksheet.write(row, 1, line['date'], header_border_format)
                worksheet.write(row, 2, line['ref'], header_border_format)
                worksheet.write(row, 3, line['name'], header_border_format)
                worksheet.write(row, 4, line['product_code'], header_border_format)
                worksheet.write(row, 5, data['account_code'] or '', header_border_format)
                worksheet.write(row, 6, line['account_id'], header_border_format)
                worksheet.write(row, 7, line['debit'], header_money)
                worksheet.write(row, 8, line['credit'], header_money)
                worksheet.write(row, 9, no_before, header_money)
                worksheet.write(row, 10, co_before, header_money)
            else:
                line_style = border_format
                line_money_style = money
                if line['account_id'] == '33311':
                    vat_lines.append(line)

                    line_style = header_border_format
                    line_money_style = header_money

                worksheet.write(row, 0, line['date'], line_style)
                worksheet.write(row, 1, line['date'], line_style)
                worksheet.write(row, 2, line['ref'], line_style)
                worksheet.write(row, 3, line['name'], line_style)
                worksheet.write(row, 4, line['product_code'], line_style)
                worksheet.write(row, 5, data['account_code'] or '', line_style)
                worksheet.write(row, 6, line['account_id'], line_style)
                worksheet.write(row, 7, line['debit'], line_money_style)
                worksheet.write(row, 8, line['credit'], line_money_style)
                worksheet.write(row, 9, no_before, line_money_style)
                worksheet.write(row, 10, co_before, line_money_style)
            row += 1

        start_line += count

        if data['order_lines'] and len(data['order_lines']) > 0:
            sale_label = 'CHI TIẾT HÀNG HOÁ'
            worksheet.merge_range(start_line + 1, 0, start_line + 1, 8, sale_label, header_bold_color)

            start_line += 1
            worksheet.write(start_line + 1, 0, 'Ngày', header_border_format)
            worksheet.write(start_line + 1, 1, 'Số đơn hàng', header_border_format)
            worksheet.write(start_line + 1, 2, 'Mã hàng', header_border_format)
            worksheet.write(start_line + 1, 3, 'Tên hàng', header_border_format)
            worksheet.write(start_line + 1, 4, 'ĐVT', header_border_format)
            worksheet.write(start_line + 1, 5, 'SL', header_border_format)
            worksheet.write(start_line + 1, 6, 'Đơn giá (giá in ra phiếu xuất)', header_border_format)
            worksheet.write(start_line + 1, 7, 'VAT', header_border_format)
            worksheet.write(start_line + 1, 8, 'Tổng', header_border_format)

            row = start_line + 2
            price_subtotal = 0
            for order_line in data['order_lines']:
                if data['account_code'] == '131':
                    price_unit = order_line.price_subtotal / order_line.product_uom_qty
                    if order_line.order_id.sale_order_return:
                        worksheet.write(row, 0, order_line.date_order, border_format)
                        worksheet.write(row, 1, order_line.order_id.name, border_format)
                        worksheet.write(row, 2, order_line.product_id.default_code, border_format)
                        worksheet.write(row, 3, order_line.product_id.name, border_format)
                        worksheet.write(row, 4, order_line.product_uom.name, border_format)
                        worksheet.write(row, 5, - order_line.product_uom_qty, border_format)
                        worksheet.write(row, 6, price_unit, money)
                        worksheet.write(row, 7, order_line.tax_sub, border_format)
                        worksheet.write(row, 8, - order_line.price_subtotal, money)
                        price_subtotal -= order_line.price_subtotal
                    else:
                        worksheet.write(row, 0, order_line.date_order, border_format)
                        worksheet.write(row, 1, order_line.order_id.name, border_format)
                        worksheet.write(row, 2, order_line.product_id.default_code, border_format)
                        worksheet.write(row, 3, order_line.product_id.name, border_format)
                        worksheet.write(row, 4, order_line.product_uom.name, border_format)
                        worksheet.write(row, 5, order_line.product_uom_qty, border_format)
                        worksheet.write(row, 6, price_unit, money)
                        worksheet.write(row, 7, order_line.tax_sub, border_format)
                        worksheet.write(row, 8, order_line.price_subtotal, money)
                        price_subtotal += order_line.price_subtotal
                elif data['account_code'] == '331':
                    price_unit = order_line.price_subtotal / order_line.product_qty
                    if order_line.order_id.purchase_order_return:
                        worksheet.write(row, 0, order_line.date_planned, border_format)
                        worksheet.write(row, 1, order_line.order_id.name, border_format)
                        worksheet.write(row, 2, order_line.product_id.default_code, border_format)
                        worksheet.write(row, 3, order_line.product_id.name, border_format)
                        worksheet.write(row, 4, order_line.product_uom.name, border_format)
                        worksheet.write(row, 5, - order_line.product_qty, border_format)
                        worksheet.write(row, 6, price_unit, money)
                        worksheet.write(row, 7, order_line.tax_sub, border_format)
                        worksheet.write(row, 8, - order_line.price_subtotal, money)
                        price_subtotal -= order_line.price_subtotal
                    else:
                        worksheet.write(row, 0, order_line.date_planned, border_format)
                        worksheet.write(row, 1, order_line.order_id.name, border_format)
                        worksheet.write(row, 2, order_line.product_id.default_code, border_format)
                        worksheet.write(row, 3, order_line.product_id.name, border_format)
                        worksheet.write(row, 4, order_line.product_uom.name, border_format)
                        worksheet.write(row, 5, order_line.product_qty, border_format)
                        worksheet.write(row, 6, price_unit, money)
                        worksheet.write(row, 7, order_line.tax_sub, border_format)
                        worksheet.write(row, 8, order_line.price_subtotal, money)
                        price_subtotal += order_line.price_subtotal
                row += 1

            worksheet.merge_range(row, 0, row, 7, 'Tổng', header_bold_color)
            worksheet.write(row, 8, price_subtotal, header_money)
        #
        # worksheet.set_column('B:B', None, None, {'hidden': True})
        # worksheet.set_column('C:C', None, None, {'hidden': True})
        # worksheet.set_column('D:D', None, None, {'hidden': True})
        # worksheet.set_column('E:E', None, None, {'hidden': True})
        # worksheet.set_column('G:G', None, None, {'hidden': True})
        # worksheet.set_column('J:J', None, None, {'hidden': True})

        start_line = row + 2

        if len(vat_lines) > 0:
            sale_label = 'VAT'
            worksheet.merge_range(start_line, 0, start_line, 8, sale_label, header_bold_color)
            start_line += 1

            worksheet.merge_range('A%s:A%s' % (start_line + 1, start_line + 2), "Ngày hạch toán",
                                  header_border_format)
            worksheet.merge_range('B%s:B%s' % (start_line + 1, start_line + 2), "Ngày chứng từ",
                                  header_border_format)
            worksheet.merge_range('C%s:C%s' % (start_line + 1, start_line + 2), "Số chứng từ", header_border_format)
            worksheet.merge_range('D%s:D%s' % (start_line + 1, start_line + 2), "Diễn giải", header_border_format)
            worksheet.merge_range('E%s:E%s' % (start_line + 1, start_line + 2), "Mã hàng", header_border_format)
            worksheet.merge_range('F%s:F%s' % (start_line + 1, start_line + 2), "TK công nợ", header_border_format)
            worksheet.merge_range('G%s:G%s' % (start_line + 1, start_line + 2), "TK đối ứng", header_border_format)
            worksheet.merge_range('H%s:I%s' % (start_line + 1, start_line + 1), "Phát sinh", header_border_format)
            worksheet.write(start_line + 1, 7, "Nợ", header_border_format)
            worksheet.write(start_line + 1, 8, "Có", header_border_format)

            total_debit = 0
            total_credit = 0
            row = start_line + 2
            for line in vat_lines:
                worksheet.write(row, 0, line['date'], header_border_format)
                worksheet.write(row, 1, line['date'], header_border_format)
                worksheet.write(row, 2, line['ref'], header_border_format)
                worksheet.write(row, 3, line['name'], header_border_format)
                worksheet.write(row, 4, line['product_code'], header_border_format)
                worksheet.write(row, 5, data['account_code'] or '', header_border_format)
                worksheet.write(row, 6, line['account_id'], header_border_format)
                worksheet.write(row, 7, line['debit'], header_money)
                worksheet.write(row, 8, line['credit'], header_money)
                total_debit += line['debit']
                total_credit += line['credit']

                row += 1

            worksheet.merge_range(row, 0, row, 6, 'Tổng', header_bold_color)
            worksheet.write(row, 7, total_debit, header_money)
            worksheet.write(row, 8, total_credit, header_money)

        return start_line

    def round_number(self, number):
        return number
        # return math.floor(number / 100) * 100

    def no_accent_vietnamese(self, s, truncate=False):
        if truncate:
            if len(s) > 25:
                names = s.split(' ')
                length = len(names) - 4
                if length > 0:
                    s = ' '.join(names[length:])
        return s  # .encode('utf-8')

    @api.model
    def get_order_data(self, data, partner, force_null=True):
        start_date = end_date = False
        if data['start_date']:
            start_date = (datetime.strptime(data['start_date'], "%d/%m/%Y")).strftime(DEFAULT_SERVER_DATE_FORMAT)

        if data['end_date']:
            end_date = (datetime.strptime(data['end_date'], "%d/%m/%Y")).strftime(DEFAULT_SERVER_DATE_FORMAT)
        conditions = []
        if partner and partner.id:
            conditions.append(('order_partner_id', '=', partner.id))
        elif force_null:
            conditions.append(('order_partner_id', '=', False))

        order_lines = []
        if data['code'] == '131':
            conditions.append(('state', '=', 'sale'))
            if start_date:
                conditions.append(('date_order', '>=', start_date))
            if end_date:
                conditions.append(('date_order', '<=', end_date))
            order_lines = self.env['sale.order.line'].search(conditions, order='date_order asc')
        elif data['code'] == '331':
            conditions.append(('state', '=', 'purchase'))
            if start_date:
                conditions.append(('date_planned', '>=', start_date))
            if end_date:
                conditions.append(('date_planned', '<=', end_date))
            order_lines = self.env['purchase.order.line'].search(conditions, order='date_planned asc')

        return order_lines

    @api.model
    def get_data_report(self, data, partner, force_null=False):

        account_id = data['code']
        if account_id:
            account_id = self.env['account.account'].search([
                ('code', '=', account_id)
            ], limit=1)

        account_code = account_id.code

        conditions = [('account_id.code', '=', account_code)]
        conditions_before = [('account_id.code', '=', account_code)]
        if data['start_date']:
            start_date = (datetime.strptime(data['start_date'], "%d/%m/%Y")).strftime(DEFAULT_SERVER_DATE_FORMAT)
            conditions.append(('date', '>=', start_date))
            conditions_before.append(('date', '<', start_date))
        if data['end_date']:
            end_date = (datetime.strptime(data['end_date'], "%d/%m/%Y")).strftime(DEFAULT_SERVER_DATE_FORMAT)
            conditions.append(('date', '<=', end_date))
        #
        if partner:
            conditions.append(('partner_id', '=', partner.id))
            conditions_before.append(('partner_id', '=', partner.id))
        elif force_null:
            conditions.append(('partner_id', '=', False))
            conditions_before.append(('partner_id', '=', False))

        no_before = 0.0
        co_before = 0.0
        if data['start_date']:
            lines = self.env['account.move.line'].search(conditions_before, order='date asc')
            for line in lines:
                if line.account_id.code == account_code:
                    no_before += line.debit
                    co_before += line.credit

        no_before = self.round_number(no_before)
        co_before = self.round_number(co_before)

        no_current = 0.0
        co_current = 0.0
        cong_no_report = []
        data_line_report = []
        # moves = self.env['account.move'].search(conditions, order='date asc')
        moves = self.env['account.move.line'].search(conditions, order='date asc').mapped('move_id')
        for account_move in moves:
            line_current_account = False
            for data_line in account_move.line_ids:
                if partner:
                    if data_line.account_id.code == account_code and data_line.partner_id == partner:
                        no_current += data_line.debit
                        co_current += data_line.credit

                        list = {
                            'date': data_line.date,
                            'move_id': data_line.move_id.name,
                            'journal_id': data_line.journal_id.display_name,
                            'name': data_line.name,
                            'ref': data_line.ref or account_move.name,
                            'partner_id': data_line.partner_id.name,
                            'account_id': data_line.account_id.code,
                            'debit': data_line.debit,
                            'credit': data_line.credit,
                            'date_maturity': data_line.date_maturity,
                            'product_id': data_line.product_id,
                            'product_code': data_line.product_id and data_line.product_id.default_code or '',
                        }
                        cong_no_report.append(list)
                        line_current_account = list
                else:
                    if data_line.account_id.code == account_code:
                        no_current += data_line.debit
                        co_current += data_line.credit

                        list = {
                            'date': data_line.date,
                            'move_id': data_line.move_id.name,
                            'journal_id': data_line.journal_id.display_name,
                            'name': data_line.name,
                            'ref': data_line.ref or account_move.name,
                            'partner_id': data_line.partner_id.name,
                            'account_id': data_line.account_id.code,
                            'debit': data_line.debit,
                            'credit': data_line.credit,
                            'date_maturity': data_line.date_maturity,
                            'product_id': data_line.product_id,
                            'product_code': data_line.product_id and data_line.product_id.default_code or '',
                        }
                        cong_no_report.append(list)
                        line_current_account = list
            for data_line in account_move.line_ids:
                if data_line.account_id.code != account_code :
                    if (line_current_account.get('debit', 0) and data_line.credit):
                        list = {
                            'date': data_line.date,
                            'move_id': data_line.move_id.name,
                            'journal_id': data_line.journal_id.display_name,
                            'name': data_line.name,
                            'ref': data_line.ref or account_move.name,
                            'partner_id': data_line.partner_id.name,
                            'account_id': data_line.account_id.code,
                            'debit': data_line.credit if data_line.credit <= line_current_account.get(
                                'debit') else line_current_account.get('debit'),
                            'credit': data_line.debit,
                            'date_maturity': data_line.date_maturity,
                            'product_id': data_line.product_id,
                            'product_code': data_line.product_id and data_line.product_id.default_code or '',
                        }
                        data_line_report.append(list)
                    elif (line_current_account.get('credit', 0) and data_line.debit):
                        list = {
                            'date': data_line.date,
                            'move_id': data_line.move_id.name,
                            'journal_id': data_line.journal_id.display_name,
                            'name': data_line.name,
                            'ref': data_line.ref or account_move.name,
                            'partner_id': data_line.partner_id.name,
                            'account_id': data_line.account_id.code,
                            'debit': data_line.credit,
                            'credit': data_line.debit if data_line.debit <= line_current_account.get(
                                'credit') else line_current_account.get('credit'),
                            'date_maturity': data_line.date_maturity,
                            'product_id': data_line.product_id,
                            'product_code': data_line.product_id and data_line.product_id.default_code or '',
                        }
                        data_line_report.append(list)

        no_current = self.round_number(no_current)
        co_current = self.round_number(co_current)

        no_end = 0.0
        co_end = 0.0
        sum_cong_no = no_before + no_current - co_before - co_current
        if sum_cong_no < 0:
            co_end = - sum_cong_no
        else:
            no_end = sum_cong_no

        no_end = self.round_number(no_end)
        co_end = self.round_number(co_end)

        return {
            'name': partner and partner.name or '',
            'account': account_id.display_name,
            'account_code': account_id.code,
            'no_before': no_before,
            'co_before': co_before,
            'no_current': no_current,
            'co_current': co_current,
            'no_end': no_end,
            'co_end': co_end,
            'data_line_report': data_line_report,
            'cong_no_report': cong_no_report,
            'order_lines': [],
        }

    @api.model
    def print_phat_sinh_excel(self, domain_list, nodk, codk, psno, psco, nock, cock):
        output = StringIO.StringIO()
        move_line = self.env['account.move.line']
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('PhatSinh')

        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 10)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 30)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:H', 15)

        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'left', 'valign': 'vcenter'})
        money = workbook.add_format({'num_format': '#,##0','border': 1,})

        worksheet.merge_range('A1:I1', self.env.user.company_id.name or '', body_bold_color)
        worksheet.merge_range('A2:I2', self.env.user.company_id.street or '', body_bold_color)
        worksheet.merge_range('A3:I3', 'PHÁT SINH', header_bold_color)
        day_now = datetime.now().date().strftime('Ngày %d tháng %m năm %Y')
        worksheet.merge_range('A4:I4', day_now, header_bold_color)
        row = 4
        row += 1
        worksheet.write(row, 2, 'Tổng Nợ ĐK', header_bold_color)
        worksheet.write(row, 3, 'Tổng Có ĐK', header_bold_color)
        worksheet.write(row, 4, 'Tổng PS Nợ', header_bold_color)
        worksheet.write(row, 5, 'Tổng PS Có', header_bold_color)
        worksheet.write(row, 6, 'Tổng Nợ CK', header_bold_color)
        worksheet.write(row, 7, 'Tổng Có CK', header_bold_color)
        row += 1
        records = move_line.search(domain_list,order='date asc,id asc')
        worksheet.write(row, 2, nodk)
        worksheet.write(row, 3, codk)
        worksheet.write(row, 4, psno)
        worksheet.write(row, 5, psco)
        worksheet.write(row, 6, nock)
        worksheet.write(row, 7, cock)
        row += 1
        summary_header = ['Ngày hạch toán', 'Ngày chứng từ', 'Số chứng từ', 'Đối tác','Mã sản phẩm','Tên','ĐVT','SL','Đơn giá vốn', 'Tài khoản','Tài Khoản Đối Ứng', 'Nợ',
                          'Có', 'Số dư nợ', 'Số dư có']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for record in records:
            row += 1
            worksheet.write(row, 0, datetime.strptime(record.date,DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y'))
            worksheet.write(row, 1, datetime.strptime(record.date,DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y'))
            worksheet.write(row, 2, record.ref or '')
            worksheet.write(row, 3, record.partner_id.name or '')
            worksheet.write(row, 4, record.product_default_code or '')
            worksheet.write(row, 5, record.product_name or '')
            worksheet.write(row, 6, record.product_uom_id.name or '' )
            worksheet.write(row, 7, record.quantity or 0)
            worksheet.write(row, 8, record.product_price or 0,money)
            worksheet.write(row, 9, record.account_sub_code or '')
            worksheet.write(row, 10, record.account_doiung or '')
            worksheet.write(row, 11, record.debit or 0,money)
            worksheet.write(row, 12, record.credit or 0,money)
            worksheet.write(row, 13, record.so_du_no or 0,money)
            worksheet.write(row, 14, record.so_du_co or 0,money)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'PhatSinh_Excel.xlsx', 'datas_fname': 'PhatSinh_Excel.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return str(base_url) + str(download_url)

    @api.model
    def print_pnl_excel(self, domain_list):
        output = StringIO.StringIO()
        move_line = self.env['account.move.line']
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('PnL')

        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 10)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 30)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:H', 15)

        header_bold_color = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        header_bold_color.set_text_wrap(1)
        body_bold_color = workbook.add_format(
            {'bold': False, 'font_size': '14', 'align': 'left', 'valign': 'vcenter'})
        money = workbook.add_format({'num_format': '#,##0', 'border': 1, })

        worksheet.merge_range('A1:I1', self.env.user.company_id.name or '', body_bold_color)
        worksheet.merge_range('A2:I2', self.env.user.company_id.street or '', body_bold_color)
        worksheet.merge_range('A3:I3', 'BÁO CÁO PNL', header_bold_color)
        day_now = datetime.now().date().strftime('Ngày %d tháng %m năm %Y')
        worksheet.merge_range('A4:I4', day_now, header_bold_color)
        row = 4
        row += 1
        records = move_line.search(domain_list, order='date asc,id asc')

        summary_header = ['Ngày hạch toán', 'Ngày chứng từ', 'Số chứng từ', 'Đối tác', 'Mã sản phẩm', 'Sản phẩm', 'ĐVT',
                          'SL', 'Đơn giá vốn', 'Tài khoản', 'Tài Khoản Đối Ứng', 'Nợ',
                          'Có', 'Số dư nợ', 'Số dư có']

        [worksheet.write(row, header_cell, unicode(summary_header[header_cell], "utf-8"), header_bold_color) for
         header_cell in range(0, len(summary_header)) if summary_header[header_cell]]

        for record in records.with_context(args=domain_list):
            row += 1
            worksheet.write(row, 0, datetime.strptime(record.date, DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y'))
            worksheet.write(row, 1, datetime.strptime(record.date, DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y'))
            worksheet.write(row, 2, record.ref or '')
            worksheet.write(row, 3, record.partner_id.name or '')
            worksheet.write(row, 4, record.product_default_code or '')
            worksheet.write(row, 5, record.product_name or '')
            worksheet.write(row, 6, record.product_uom_id.name or '')
            worksheet.write(row, 7, record.quantity or 0)
            worksheet.write(row, 8, record.product_price or 0, money)
            worksheet.write(row, 9, record.account_sub_code or '')
            worksheet.write(row, 10, record.account_doiung or '')
            worksheet.write(row, 11, record.debit or 0, money)
            worksheet.write(row, 12, record.credit or 0, money)
            worksheet.write(row, 13, record.so_du_no or 0, money)
            worksheet.write(row, 14, record.so_du_co or 0, money)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'PnL_Excel.xlsx', 'datas_fname': 'PnL_Excel.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return str(base_url) + str(download_url)

    @api.model
    def get_debit_credit_current(self, domain_list, start_date, end_date, partner_str, context):
        domain_not_date = []
        if not domain_list:
            domain_list = []
        else:
            domain_not_date = domain_list
            if domain_not_date and any(['date' in a for a in domain_list]):
                domain_not_date = filter(lambda rec: rec[0] != 'date', domain_not_date)
        action = False

        account_112 = False
        if context and context.get('params', False):
            action = context.get('params', False).get('action', False)
        if action and action == self.env.ref("tuanhuy_account_reports.account_move_112_report_action")[0].id:
            account_112 = False
        #     bao cao hdkd => journals
        if context.get('context',False):
            if context['context'].get('date_from',False):
                start_date = datetime.strptime(context['context'].get('date_from',False),DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y')
            if context['context'].get('date_to',False):
                end_date = datetime.strptime(context['context'].get('date_to', False),DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y')
        move_ids = self.sudo().search(domain_not_date)
        no_before = co_before = 0
        no_before_value = co_before_value = 0
        no_current = co_current = 0
        no_value = co_value = 0
        co_ck = no_ck = 0
        if move_ids:
            query_before = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                                        FROM account_move_line aml WHERE id in (%s)""" %(', '.join(str(move_id) for move_id in move_ids.ids))

            query = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                            FROM account_move_line aml WHERE id in (%s) """ %(', '.join(str(move_id) for move_id in move_ids.ids))

            if start_date:
                start_date = (datetime.strptime(start_date, "%d/%m/%Y")).strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
                query_before += """ AND aml.date < '%s' """ % start_date
                query += """ AND aml.date >= '%s' """ % start_date

            if end_date:
                end_date = (datetime.strptime(end_date, "%d/%m/%Y")).strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
                query += """ AND aml.date <= '%s' """ % end_date
            if partner_str:
                customer_ids = []
                name_upper = partner_str.upper()
                self.env.cr.execute(
                    "select id from res_partner where upper(name) = '%s'" % (name_upper))
                res_trans = self.env.cr.fetchall()
                for line in res_trans:
                    customer_ids.append(line[0])
                if customer_ids:
                    query_before += """ AND aml.partner_id in (%s) """ % (', '.join(str(id) for id in customer_ids))
                    query += """ AND aml.partner_id in (%s) """ % (', '.join(str(id) for id in customer_ids))
            if start_date:
                self.env.cr.execute(query_before)
                move_before = self.env.cr.fetchall()
                if move_before and len(move_before) > 0:
                    if move_before[0][0] or move_before[0][1]:
                        no_before = move_before[0][0]
                        co_before = move_before[0][1]
                if (no_before - co_before) > 0:
                    no_before_value = no_before - co_before
                    co_before_value = 0
                else:
                    no_before_value = 0
                    co_before_value = co_before - no_before

            self.env.cr.execute(query)
            move_current = self.env.cr.fetchall()
            if move_current and len(move_current) > 0:
                if move_current[0][0] or move_current[0][1]:
                    no_current = move_current[0][0]
                    co_current = move_current[0][1]
            no_value = no_before_value + no_current
            co_value = co_before_value + co_current
            no_ck = co_ck = 0
            if no_value > co_value:
                no_ck = no_value - co_value
                co_ck = 0
            else:
                co_ck = co_value - no_value
                no_ck = 0
        if account_112:
            return '{0:,.2f}'.format(co_current), '{0:,.2f}'.format(no_current), '{0:,.2f}'.format(co_ck), '{0:,.2f}'.format(no_ck)
        return '{0:,.2f}'.format(no_current), '{0:,.2f}'.format(co_current), '{0:,.2f}'.format(
            no_ck), '{0:,.2f}'.format(co_ck)

    @api.model
    def get_debit_credit_before(self, domain_list, start_date, partner_str, context):
        account_code = False
        partner_ids = False
        ref = product_code = move_id = False
        no_before_value = co_before_value = 0
        domain_not_date = []
        account_id = account_ids = False
        if not domain_list:
            domain_list = []
        else:
            domain_not_date = domain_list
            if domain_not_date and any(['date' in a for a in domain_list]):
                domain_not_date = filter(lambda rec: rec[0] != 'date', domain_not_date)
        action = False
        account_112 = False
        if context and context.get('params', False):
            action = context.get('params', False).get('action', False)
        if action and action == self.env.ref("tuanhuy_account_reports.account_move_112_report_action")[0].id:
            account_112 = False
            #     bao cao hdkd => journals
        if context.get('context',False):
            if context['context'].get('date_from',False):
                start_date = datetime.strptime(context['context'].get('date_from',False),DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y')
            if context['context'].get('date_to',False):
                end_date = datetime.strptime(context['context'].get('date_to', False),DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y')
        move_ids = self.search(domain_not_date)
        if move_ids:
            start_date = (datetime.strptime(start_date, "%d/%m/%Y")).strftime(DEFAULT_SERVER_DATE_FORMAT) if start_date else False

            no_before = co_before = 0

            query = """SELECT SUM(aml.debit) AS debit, SUM(aml.credit) AS credit
                                       FROM account_move_line aml 
                                       WHERE aml.id in (%s) """ % (', '.join(str(id.id) for id in move_ids))
            if start_date:
                query += " AND aml.date < '%s' " %(start_date)
            if partner_str:
                customer_ids = []
                name_upper = partner_str.upper()
                self.env.cr.execute(
                    "select id from res_partner where upper(name) = '%s'" % (name_upper))
                res_trans = self.env.cr.fetchall()
                for line in res_trans:
                    customer_ids.append(line[0])
                if customer_ids:
                    query += """
                           AND aml.partner_id in (%s)
                       """ % (', '.join(str(id) for id in customer_ids))
            if start_date:
                self.env.cr.execute(query)
                move_before = self.env.cr.fetchall()
                if move_before and len(move_before) > 0:
                    if move_before[0][0] or move_before[0][1]:
                        no_before = move_before[0][0]
                        co_before = move_before[0][1]
                if (no_before - co_before) > 0:
                    no_before_value = no_before - co_before
                    co_before_value = 0
                else:
                    no_before_value = 0
                    co_before_value = co_before - no_before
        if account_112:
            return '{0:,.2f}'.format(co_before_value), '{0:,.2f}'.format(no_before_value)
        return '{0:,.2f}'.format(no_before_value), '{0:,.2f}'.format(co_before_value)

    @api.model
    def get_account_xlsx(self, domain_list, nodk, codk, psno, psco, nock, cock, context):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Sheet1')
        current_data = self.search(domain_list, order='date asc, ref asc')  # , order='partner_id asc, date asc'
        account_ids = account_id = False
        account_code = list(set(current_data.mapped('account_id.code')))
        account_code_str = (', '.join(code for code in account_code))
        action = False
        account_112 = False
        if context and context.get('params',False):
            action = context.get('params',False).get('action',False)
        if action and action == self.env.ref("tuanhuy_account_reports.account_move_112_report_action")[0].id:
            account_code_str = '112'
            account_112 = False
        header_body_color = workbook.add_format({
            'bold': True,
            'font_size': '11',
            'align': 'center',
            'valign': 'vcenter',
        })
        header_bold_color = workbook.add_format({
            'bold': True,
            'font_size': '11',
            'align': 'left',
            'valign': 'vcenter',
            'bg_color': 'cce0ff',
            'border': 1,
        })
        body_bold_table = workbook.add_format(
            {'bold': False, 'border': 1, 'font_size': '12', 'align': 'left', 'valign': 'vcenter'})
        title_report = workbook.add_format(
            {'bold': True, 'font_size': '14', 'align': 'center', 'valign': 'vcenter'})
        money = workbook.add_format({
            'num_format': '#,##0',
            'border': 1,
        })
        if not account_112:
            if all(code in ('1561', '632') for code in account_code) :
                back_color = 'A1:G1'

                worksheet.set_column('A:A', 15)
                worksheet.set_column('B:B', 15)
                worksheet.set_column('C:C', 15)
                worksheet.set_column('D:D', 30)
                worksheet.set_column('E:E', 15)
                worksheet.set_column('F:F', 60)
                worksheet.set_column('G:N', 15)

                worksheet.merge_range('A1:G1', ("SỔ CHI TIẾT CÁC TÀI KHOẢN %s" % account_code_str),
                                      title_report) if account_id else worksheet.merge_range('A1:G1', (
                    "SỔ CHI TIẾT CÁC TÀI KHOẢN %s" % account_code_str), title_report)
                worksheet.merge_range('A2:G2', (
                    "Tài khoản: %s;" % account_code_str),
                                      header_body_color)

                header = [
                    'Ngày hạch toán',
                    'Ngày chứng từ',
                    'Số chứng từ',
                    'Đối tác',
                    'Mã sản phẩm',
                    'Tên sản phẩm',
                    'Đơn giá',
                    'SL',
                    'Tài khoản',
                    'TK đối ứng',
                    'Phát sinh Nợ',
                    'Phát sinh Có',
                    'Dư Nợ',
                    'Dư Có'
                ]
                row = 3

                [worksheet.write(row, header_cell, (header[header_cell]), header_bold_color) for
                 header_cell in
                 range(0, len(header)) if header[header_cell]]

                row += 1
                worksheet.write(row, 10, ("Số dư đầu kỳ"), body_bold_table)
                worksheet.write(row, 11, account_code_str, body_bold_table)
                worksheet.write(row, 12, nodk, money)
                worksheet.write(row, 13, codk, money)

                data_line_report = []

                for data_line in current_data:
                    row += 1

                    line_name = data_line.name
                    if line_name == '/':
                        if data_line.ref:
                            if 'SO' in data_line.ref:
                                line_name = 'Bán hàng'
                            elif 'PO' in data_line.ref:
                                line_name = 'Mua hàng'
                            elif 'RTP' in data_line.ref:
                                line_name = 'Trả hàng mua'
                            elif 'RT0' in data_line.ref:
                                line_name = 'Trả hàng bán'
                        else:
                            if data_line.account_id.code == '331':
                                line_name = 'Bán hàng'

                    worksheet.write(row, 0, data_line.date, body_bold_table)
                    worksheet.write(row, 1, data_line.date, body_bold_table)
                    worksheet.write(row, 2, data_line.ref or '', body_bold_table)
                    worksheet.write(row, 3, data_line.partner_id and data_line.partner_id.name or '', body_bold_table)
                    worksheet.write(row, 4, data_line.product_id.default_code, body_bold_table)
                    worksheet.write(row, 5, data_line.product_id.name, body_bold_table)
                    worksheet.write(row, 6, data_line.product_price, body_bold_table)
                    worksheet.write(row, 7, data_line.quantity, body_bold_table)
                    worksheet.write(row, 8, data_line.account_id.code, body_bold_table)
                    worksheet.write(row, 9, data_line.account_doiung, body_bold_table)
                    worksheet.write(row, 10, data_line.debit, money)
                    worksheet.write(row, 11, data_line.credit, money)
                    worksheet.write(row, 12, data_line.so_du_no, money)
                    worksheet.write(row, 13, data_line.so_du_co, money)

                row += 1
                worksheet.write(row, 7, ("Cộng"), body_bold_table)
                worksheet.write(row, 8, account_code_str, body_bold_table)
                worksheet.write(row, 9, "", body_bold_table)
                worksheet.write(row, 10, psno, money)
                worksheet.write(row, 11, psco, money)
                worksheet.write(row, 12, "", body_bold_table)
                worksheet.write(row, 13, "", body_bold_table)

                row += 1
                worksheet.write(row, 4, ("Số dư cuối kỳ"), body_bold_table)
                worksheet.write(row, 5, account_code_str, body_bold_table)
                worksheet.write(row, 6, "", body_bold_table)
                worksheet.write(row, 7, "", body_bold_table)
                worksheet.write(row, 8, "", body_bold_table)
                worksheet.write(row, 9, nock, money)
                worksheet.write(row, 10, cock, money)
            else:
                back_color = 'A1:G1'

                worksheet.set_column('A:A', 15)
                worksheet.set_column('B:B', 15)
                worksheet.set_column('C:C', 15)
                worksheet.set_column('D:D', 30)
                worksheet.set_column('E:E', 60)
                worksheet.set_column('F:F', 15)
                worksheet.set_column('G:G', 15)
                worksheet.set_column('H:H', 15)
                worksheet.set_column('I:I', 15)
                worksheet.set_column('J:J', 15)
                worksheet.set_column('K:K', 15)
                worksheet.set_column('H:H', 15)

                worksheet.merge_range('A1:G1', ("SỔ CHI TIẾT CÁC TÀI KHOẢN %s" % (account_id.code)),
                                      title_report) if account_id else worksheet.merge_range('A1:G1', (
                    "SỔ CHI TIẾT CÁC TÀI KHOẢN %s" % account_code_str), title_report)
                worksheet.merge_range('A2:G2', (
                    "Tài khoản: %s;" % account_code_str),
                                      header_body_color)

                header = [
                    'Ngày hạch toán',
                    'Ngày chứng từ',
                    'Số chứng từ',
                    'Đối tác',
                    'Diễn giải',
                    'Tài khoản',
                    'TK đối ứng',
                    'Phát sinh Nợ',
                    'Phát sinh Có',
                    'Dư Nợ',
                    'Dư Có'
                ]
                row = 3

                [worksheet.write(row, header_cell, (header[header_cell]), header_bold_color) for
                 header_cell in
                 range(0, len(header)) if header[header_cell]]

                row += 1
                worksheet.write(row, 4, ("Số dư đầu kỳ"), body_bold_table)
                worksheet.write(row, 5, account_code_str, body_bold_table)
                worksheet.write(row, 9, nodk, money)
                worksheet.write(row, 10, codk, money)

                for data_line in current_data.with_context(args=domain_list):
                    row += 1

                    line_name = data_line.name
                    if line_name == '/':
                        if data_line.ref:
                            if 'SO' in data_line.ref:
                                line_name = 'Bán hàng'
                            elif 'PO' in data_line.ref:
                                line_name = 'Mua hàng'
                            elif 'RTP' in data_line.ref:
                                line_name = 'Trả hàng mua'
                            elif 'RT0' in data_line.ref:
                                line_name = 'Trả hàng bán'
                        else:
                            if data_line.account_id.code == '331':
                                line_name = 'Bán hàng'

                    worksheet.write(row, 0, data_line.date, body_bold_table)
                    worksheet.write(row, 1, data_line.date, body_bold_table)
                    worksheet.write(row, 2, data_line.ref or '', body_bold_table)
                    worksheet.write(row, 3, data_line.partner_id and data_line.partner_id.name or '', body_bold_table)
                    worksheet.write(row, 4, line_name, body_bold_table)
                    worksheet.write(row, 5, data_line.account_id.code, body_bold_table)
                    worksheet.write(row, 6, data_line.account_doiung, body_bold_table)
                    worksheet.write(row, 7, data_line.debit, money)
                    worksheet.write(row, 8, data_line.credit, money)
                    worksheet.write(row, 9, data_line.so_du_no, money)
                    worksheet.write(row, 10, data_line.so_du_co, money)

                row += 1
                worksheet.write(row, 4, ("Cộng"), body_bold_table)
                worksheet.write(row, 5, account_code_str, body_bold_table)
                worksheet.write(row, 6, "", body_bold_table)
                worksheet.write(row, 7, psno, money)
                worksheet.write(row, 8, psco, money)
                worksheet.write(row, 9, "", body_bold_table)
                worksheet.write(row, 10, "", body_bold_table)

                row += 1
                worksheet.write(row, 4, ("Số dư cuối kỳ"), body_bold_table)
                worksheet.write(row, 5, account_code_str, body_bold_table)
                worksheet.write(row, 6, "", body_bold_table)
                worksheet.write(row, 7, "", body_bold_table)
                worksheet.write(row, 8, "", body_bold_table)
                worksheet.write(row, 9, nock, money)
                worksheet.write(row, 10, cock, money)
        else:
            # print bao cao tai khoan 112
            worksheet.set_column('A:A', 15)
            worksheet.set_column('B:B', 15)
            worksheet.set_column('C:C', 15)
            worksheet.set_column('D:D', 30)
            worksheet.set_column('E:E', 60)
            worksheet.set_column('F:F', 15)
            worksheet.set_column('G:G', 15)
            worksheet.set_column('H:H', 15)
            worksheet.set_column('I:I', 15)
            worksheet.set_column('J:J', 15)
            worksheet.set_column('K:K', 15)
            worksheet.set_column('H:H', 15)

            worksheet.merge_range('A1:G1', ("SỔ CHI TIẾT CÁC TÀI KHOẢN %s" % (account_id.code)),
                                  title_report) if account_id else worksheet.merge_range('A1:G1', (
                "SỔ CHI TIẾT CÁC TÀI KHOẢN %s" % account_code_str), title_report)
            worksheet.merge_range('A2:G2', (
                "Tài khoản: %s;" % account_code_str),
                                  header_body_color)

            header = [
                'Ngày hạch toán',
                'Ngày chứng từ',
                'Số chứng từ',
                'Đối tác',
                'Diễn giải',
                'Tài khoản',
                'TK đối ứng',
                'Phát sinh Nợ',
                'Phát sinh Có',
                'Luỹ kế'
            ]
            row = 3

            [worksheet.write(row, header_cell, (header[header_cell]), header_bold_color) for
             header_cell in
             range(0, len(header)) if header[header_cell]]

            row += 1
            worksheet.write(row, 4, ("Số dư đầu kỳ"), body_bold_table)
            worksheet.write(row, 5, account_code_str, body_bold_table)
            worksheet.write(row, 9, nodk, money)
            worksheet.write(row, 10, codk, money)

            for data_line in current_data.with_context(args=domain_list):
                row += 1

                line_name = data_line.name
                if line_name == '/':
                    if data_line.ref:
                        if 'SO' in data_line.ref:
                            line_name = 'Bán hàng'
                        elif 'PO' in data_line.ref:
                            line_name = 'Mua hàng'
                        elif 'RTP' in data_line.ref:
                            line_name = 'Trả hàng mua'
                        elif 'RT0' in data_line.ref:
                            line_name = 'Trả hàng bán'
                    else:
                        if data_line.account_id.code == '331':
                            line_name = 'Bán hàng'

                worksheet.write(row, 0, data_line.date, body_bold_table)
                worksheet.write(row, 1, data_line.date, body_bold_table)
                worksheet.write(row, 2, data_line.ref or '', body_bold_table)
                worksheet.write(row, 3, data_line.partner_id and data_line.partner_id.name or '', body_bold_table)
                worksheet.write(row, 4, line_name, body_bold_table)
                worksheet.write(row, 5, data_line.account_id.code, body_bold_table)
                worksheet.write(row, 6, data_line.account_doiung, body_bold_table)
                worksheet.write(row, 7, data_line.debit, money)
                worksheet.write(row, 8, data_line.credit, money)
                worksheet.write(row, 9, data_line.luy_ke_112, money)

            row += 1
            worksheet.write(row, 4, ("Cộng"), body_bold_table)
            worksheet.write(row, 5, account_code_str, body_bold_table)
            worksheet.write(row, 6, "", body_bold_table)
            worksheet.write(row, 7, psno, money)
            worksheet.write(row, 8, psco, money)
            worksheet.write(row, 9, "", body_bold_table)
            worksheet.write(row, 10, "", body_bold_table)

            row += 1
            worksheet.write(row, 4, ("Số dư cuối kỳ"), body_bold_table)
            worksheet.write(row, 5, account_code_str, body_bold_table)
            worksheet.write(row, 6, "", body_bold_table)
            worksheet.write(row, 7, "", body_bold_table)
            worksheet.write(row, 8, "", body_bold_table)
            worksheet.write(row, 9, nock, money)
            worksheet.write(row, 10, cock, money)

        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': '%s_Excel.xlsx' %(account_code_str), 'datas_fname': '%s_Excel.xlsx' %(account_code_str), 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return str(base_url) + str(download_url)