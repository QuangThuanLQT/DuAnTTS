# -*- coding: utf-8 -*-
from odoo import models, fields, api
import pytz
import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
from odoo import tools
from lxml import etree

class stock_inventory_report(models.TransientModel):
    _name = 'tong.hop.cong.no.popup'

    date_start      = fields.Date(string='Từ ngày')
    date_to        = fields.Date(string='Đến Ngày')
    type            = fields.Selection([('done','Trạng thái hoàn thành'),('all','Tất cả trạng thái')],string='Loại',required=True,default='done')
    account_type    = fields.Selection([('thu','Khoản phải thu'),('tra','Phải trả'),('tam_ung','Tạm ứng'),('khoan_khac','Khoản thu khác'),('khoan_tra_khac','Khoản trả khác')],string='Loại tài khoản',required=True,default='thu')

    @api.multi
    def open_cong_no_phai_tra(self):
        account_id = self.env['account.account']
        result_context = {}
        result_domain = []
        action = self.env.ref('tong_hop_cong_no_report.action_th_cong_no_phai_tra_report').read()[0]

        if self.date_start:
            result_context.update({'congno_date_from': self.date_start})

        if self.date_to:
            result_context.update({'congno_date_to': self.date_to})

        if not self.date_start and not self.date_to:
            result_context.update({'congno': True})
        if self.account_type == 'thu':
            account_id = self.env['account.account'].sudo().search([('user_type_id.type','=','receivable')])
            result_context.update({'search_default_customer': True})
        elif self.account_type == 'tra':
            account_id = self.env['account.account'].sudo().search([('user_type_id.type', '=', 'payable')])
            result_context.update({'search_default_supplier': True})
        elif self.account_type == 'khoan_khac':
            account_id = self.env['account.account'].sudo().search([('code', '=like', '138%')])
            self.env.cr.execute("""SELECT partner_id from account_move_line where account_id in (%s)"""%(', '.join(str(account) for account in account_id.ids)))
            partner_ids = [partner[0] for partner in self.env.cr.fetchall()]
            action['domain'] = [('partner_id', 'in', partner_ids)]
        elif self.account_type == 'khoan_tra_khac':
            account_id = self.env['account.account'].sudo().search([('code', '=like', '338%')])
            self.env.cr.execute("""SELECT partner_id from account_move_line where account_id in (%s)"""%(', '.join(str(account) for account in account_id.ids)))
            partner_ids = [partner[0] for partner in self.env.cr.fetchall()]
            action['domain'] = [('partner_id', 'in', partner_ids)]
        else:
            account_id = self.env['account.account'].sudo().search([('code', '=', '141')])
            self.env.cr.execute("""SELECT partner_id from account_move_line where account_id in (%s)"""%(', '.join(str(account) for account in account_id.ids)))
            partner_ids = [partner[0] for partner in self.env.cr.fetchall()]
            # partner_ids = self.env['account.move.line'].search([('account_id','in',account_id.ids)]).mapped('partner_id.id')
            action['domain'] = [('partner_id','in',partner_ids)]
        result_context.update({'congno_type': self.type})
        result_context.update({'account_id': account_id.ids or False})
        result_context.update({'account_type': self.account_type or False})


        action['context'] = str(result_context)

        return action

class cong_no_phai_tra_report(models.Model):
    _name = 'tong.hop.cong.no.report'
    _auto = False

    partner_id      = fields.Many2one('res.partner', string='Khách hàng/ Nhà cung cấp')
    account_ids     = fields.Many2many('account.account',string='TK công nợ',compute='compute_cong_no_phai_tra')
    account_name    = fields.Char(string='TK công nợ',compute='compute_cong_no_phai_tra')
    ref             = fields.Char(string='Mã Khách hàng/ Nhà cung cấp')
    name            = fields.Char(string='Khách hàng/ Nhà cung cấp')
    customer        = fields.Boolean('Khách hàng')
    bank            = fields.Boolean('Ngân hàng')
    supplier        = fields.Boolean('Nhà cung cấp')
    employee        = fields.Boolean('Người lao động')
    move_ids        = fields.Many2many('account.move.line',compute='compute_cong_no_phai_tra')
    before_debit = fields.Float(string='Nợ đầu kì', compute='compute_cong_no_phai_tra')
    before_credit = fields.Float(string='Có đầu kì', compute='compute_cong_no_phai_tra')

    current_debit = fields.Float(string='Phát sinh nợ', compute='compute_cong_no_phai_tra')
    current_credit = fields.Float(string='Phát sinh có', compute='compute_cong_no_phai_tra')

    after_debit = fields.Float(string='Nợ cuối kì', compute='compute_cong_no_phai_tra')
    after_credit = fields.Float(string='Có cuối kì', compute='compute_cong_no_phai_tra')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'tong_hop_cong_no_report')
        self.env.cr.execute(
            """CREATE or REPLACE VIEW tong_hop_cong_no_report as (
            SELECT 
            min(rp.id) as id,
            rp.id as partner_id,
            rp.ref as ref,
            rp.name as name,
            COALESCE (rp.customer,FALSE ) as customer,
            COALESCE (rp.supplier,FALSE ) as supplier,
            COALESCE (rp.bank,FALSE ) as bank,
            COALESCE (rp.employee,FALSE ) as employee
            FROM res_partner as rp
            GROUP BY rp.id,rp.ref,rp.customer,rp.supplier,rp.bank,rp.employee)
            """)

    @api.multi
    def compute_cong_no_phai_tra(self):
        move_line = self.env['account.move.line'].sudo()
        context = self.env.context.copy()
        current_domain = [('account_id', 'in', context.get('account_id', False))]
        before_domain = [('account_id', 'in', context.get('account_id', False))]
        after_domain = [('account_id', 'in', context.get('account_id', False))]
        account_ids = date_from = date_to = type =  False

        if context.get('account_id',False):
            account_ids = self.env['account.account'].browse(context.get('account_id',False))

        if context.get('congno_date_from', False):
            date_from = context.get('congno_date_from', False)
            current_domain.append(('date','>=',date_from))
            before_domain.append(('date','<',date_from))

        if context.get('congno_date_to', False):
            date_to = context.get('congno_date_to', False)
            current_domain.append(('date', '<=', date_to))
            after_domain.append(('date', '>', date_to))

        if context.get('congno_type', False):
            type = context.get('congno_type', False)
            if type == 'done':
                current_domain.append(('move_id.state', '=', 'posted'))
                before_domain.append(('move_id.state', '=', 'posted'))
                after_domain.append(('move_id.state', '=', 'posted'))
            # else:
                # domain.append([('move_id.state', '!=', date_to)])

        # current_move = move_line.search(current_domain)
        # before_move = move_line.search(before_domain)
        # after_move = move_line.search(after_domain)

        for record in self:
            partner_domain = [('partner_id','=',record.partner_id.id or False)]
            before_debit = sum(move_line.search(before_domain + partner_domain).mapped('debit'))
            before_credit = sum(move_line.search(before_domain + partner_domain).mapped('credit'))
            record.before_debit = 0 if (before_credit >= before_debit) else (before_debit - before_credit)
            record.before_credit = 0 if (before_debit >= before_credit) else (before_credit - before_debit)

            record.current_debit = sum(move_line.search(current_domain + partner_domain).mapped('debit'))
            record.current_credit = sum(move_line.search(current_domain + partner_domain).mapped('credit'))
            total_debit = record.before_debit + record.current_debit
            total_credit = record.before_credit + record.current_credit
            record.after_debit = 0 if (total_credit >= total_debit) else (total_debit-total_credit)
            record.after_credit = 0 if (total_debit >= total_credit) else (total_credit-total_debit)

            record.move_ids = move_line.search(current_domain + partner_domain)
            record.account_ids = account_ids
            record.account_name = ' ,'.join(account.display_name for account in record.move_ids.mapped('account_id')) or ' ,'.join(account.display_name for account in account_ids)

    @api.multi
    def open_phat_sinh(self):
        action = self.env.ref('account.action_account_moves_all_a').read()[0]
        context = {}
        if self.account_ids and len(self.account_ids) == 1:
            context.update({'search_default_account_id': self.account_ids.id})
        else:
            action['domain'] = [('account_id','in',self.account_ids.ids)]
        if self.partner_id:
            context.update({'search_default_partner_id':self.partner_id.id})
        action['context'] = context
        return action

    @api.model
    def fields_view_get(self, view_id=None, view_type='tree', toolbar=False, submenu=False):
        res = super(cong_no_phai_tra_report, self).fields_view_get(view_id=view_id, view_type=view_type,toolbar=toolbar, submenu=submenu)

        if view_type == 'tree' and self._context.get('account_type',False):
            doc = etree.XML(res['arch'], parser=None, base_url=None)
            for node in doc.xpath("//field[@name='ref']"):
                if self._context.get('account_type') == 'thu':
                    node.set('string', unicode("Mã Khách hàng"))
                elif self._context.get('account_type') == 'tra':
                    node.set('string', unicode("Mã Nhà cung cấp"))
                elif self._context.get('account_type') in ['tam_ung','khoan_khac','khoan_tra_khac']:
                    node.set('string', unicode("Mã đối tác"))
                # elif self._context.get('account_type') == 'khoan_khac':
                #     node.set('string', unicode("Mã đối tác"))
            for node in doc.xpath("//field[@name='name']"):
                if self._context.get('account_type') == 'thu':
                    node.set('string', unicode("Khách hàng"))
                elif self._context.get('account_type') == 'tra':
                    node.set('string', unicode("Nhà cung cấp"))
                elif self._context.get('account_type') in ['tam_ung','khoan_khac','khoan_tra_khac']:
                    node.set('string', unicode("Đối tác"))
                # elif self._context.get('account_type') == 'khoan_khac':
                #     node.set('string', unicode("Đối tác"))
            res['arch'] = etree.tostring(doc)
        return res

