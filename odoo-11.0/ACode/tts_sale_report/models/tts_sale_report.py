# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools


class tts_sale_report(models.Model):
    _name = 'tts.sale.report'
    _auto = False

    name = fields.Char('Order Reference', readonly=True)
    date_order = fields.Date('Date Invoice', readonly=True)
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    amount_total = fields.Float('Tổng', readonly=True)
    amount_untaxed = fields.Float('Tổng chưa thuế', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Sales Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True)

    qty_sale_order = fields.Integer('Số lượng đơn bán')
    total_amount = fields.Float('Doanh thu')
    qty_sale_return = fields.Integer('Số lượng đơn trả')
    amount_return = fields.Float('Giá trị trả')
    net_amount = fields.Float('Danh thu thuần')
    average_order_value = fields.Float('Giá trị đơn hàng trung bình')


    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW tts_sale_report as (
            select min(so.id) as id, so.name as name,
                ai.date_invoice as date_order,
                so.partner_id as partner_id,
                so.user_id as user_id,
                so.state as state,
                so.amount_untaxed as amount_untaxed,
                so.amount_total as amount_total,
              
                0.0 as average_order_value
            from sale_order so
            left join res_partner partner on so.partner_id = partner.id
            left join res_users users on so.user_id = users.id
            RIGHT JOIN account_invoice ai on so.name = ai.origin
            WHERE so.state = 'sale'
            GROUP BY
                so.name,
                so.name,
                so.date_order,
                so.partner_id,
                so.user_id,
                so.state,
                so.amount_untaxed,
                so.amount_total,
                
                ai.date_invoice
            )""")

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):

        res = super(tts_sale_report, self).read_group(domain, fields, groupby, offset=offset,
                                                 limit=limit, orderby=orderby, lazy=lazy)
        for record in res:
            if record.get('qty_sale_order') and record.get('net_amount'):
                average_order_value = record.get('net_amount') - record.get('qty_sale_order')
                record['average_order_value'] = average_order_value
        return res