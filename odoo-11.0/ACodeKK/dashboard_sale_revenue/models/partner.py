# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from calendar import monthrange


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        res = super(res_partner, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit,
                                                   order=order)
        return res

    @api.model
    def get_domain_new_customer(self):
        domain = []
        context = {"search_default_customer": 1}

        datetime_now = datetime.now()
        start_current_month = datetime_now + timedelta(days=-(datetime_now.day - 1))
        start_date = start_current_month.strftime('%Y-%m-%d 17:00:00')
        days_in_month = monthrange(start_current_month.year, start_current_month.month)[1]
        end_date = (start_current_month + timedelta(days=days_in_month - 1)).strftime('%Y-%m-%d 17:00:00')
        employee_ceo = self.env['hr.employee'].search([('job_id.name', '=', 'CEO')])
        partner_ids = self.env['sale.order'].search(
            [('state', '=', 'sale'), ('sale_order_return', '=', False), ('confirmation_date', '>=', start_date),
             ('confirmation_date', '<', end_date)]).mapped('partner_id').ids
        domain.append(('id', 'in', partner_ids))
        if self._uid in employee_ceo.mapped('user_id').ids:
            context.update({
                'search_default_current_month': 1
            })
        else:
            context.update({
                'search_default_current_month': 1,
                'search_default_my_partner': 1,
            })
        return domain, context

    @api.model
    def get_domain_customer(self):
        domain = []
        context = {"search_default_customer": 1}

        datetime_now = datetime.now()
        start_current_month = datetime_now + timedelta(days=-(datetime_now.day - 1))
        start_date = start_current_month.strftime('%Y-%m-%d 17:00:00')
        days_in_month = monthrange(start_current_month.year, start_current_month.month)[1]
        end_date = (start_current_month + timedelta(days=days_in_month - 1)).strftime('%Y-%m-%d 17:00:00')
        employee_ceo = self.env['hr.employee'].search([('job_id.name', '=', 'CEO')])
        partner_ids = self.env['sale.order'].search(
            [('state', '=', 'sale'), ('sale_order_return', '=', False), ('confirmation_date', '>=', start_date),
             ('confirmation_date', '<', end_date)]).mapped('partner_id').ids
        domain.append(('id', 'in', partner_ids))
        if self._uid in employee_ceo.mapped('user_id').ids:
            True
        else:
            context.update({
                'search_default_my_partner': 1,
            })
        return domain, context
