# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from calendar import monthrange


class sale_orer_ihr(models.Model):
    _inherit = 'sale.order'

    con_phai_thu_store = fields.Float(string='Số tiền còn phải thu', compute='_con_phai_thu_store', store=True)

    @api.depends('amount_total', 'so_tien_da_thu')
    def _con_phai_thu_store(self):
        for rec in self:
            rec.con_phai_thu_store = rec.amount_total - rec.so_tien_da_thu

    @api.model
    def get_domain_order(self):
        domain = [('state', '=', 'sale'), ('sale_order_return', '=', False), ('trang_thai_dh', '!=', 'cancel'), ]
        context = {'hide_sale': True}

        datetime_now = datetime.now()
        start_current_month = datetime_now + timedelta(days=-(datetime_now.day - 1))
        start_date = start_current_month.strftime('%Y-%m-%d 17:00:00')
        days_in_month = monthrange(start_current_month.year, start_current_month.month)[1]
        end_date = (start_current_month + timedelta(days=days_in_month - 1)).strftime('%Y-%m-%d 17:00:00')
        domain.append(('confirmation_date', '>=', start_date))
        domain.append(('confirmation_date', '<', end_date))

        employee_ceo = self.env['hr.employee'].search([('job_id.name', '=', 'CEO')])
        if self._uid in employee_ceo.mapped('user_id').ids:
            True
        else:
            domain.append(('user_id', '=', self._uid))

        return domain, context

    @api.model
    def get_domain_order_return(self):
        domain = [('sale_order_return', '=', True), ('state', '=', 'sale'), ('trang_thai_dh', '!=', 'cancel')]
        context = {'sale_order_return': True, 'tree_view_ref': 'tts_modifier_sale.view_order_tree_return'}

        datetime_now = datetime.now()
        start_current_month = datetime_now + timedelta(days=-(datetime_now.day - 1))
        start_date = start_current_month.strftime('%Y-%m-%d 17:00:00')
        days_in_month = monthrange(start_current_month.year, start_current_month.month)[1]
        end_date = (start_current_month + timedelta(days=days_in_month - 1)).strftime('%Y-%m-%d 17:00:00')
        domain.append(('confirmation_date', '>=', start_date))
        domain.append(('confirmation_date', '<', end_date))

        employee_ceo = self.env['hr.employee'].search([('job_id.name', '=', 'CEO')])
        if self._uid in employee_ceo.mapped('user_id').ids:
            True
        else:
            domain.append(('user_id', '=', self._uid))

        return domain, context
