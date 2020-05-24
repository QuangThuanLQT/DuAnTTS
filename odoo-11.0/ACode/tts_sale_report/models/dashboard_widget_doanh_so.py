# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools
from datetime import datetime, timedelta

# class widget_doanh_so(models.Model):
#     _name = 'widget.doanh.so'
#     _auto = False
#
#     date_order = fields.Datetime('Comfirmation Date', readonly=True)
#     amount_total = fields.Float('Tổng tiền', readonly=True)
#
#     @api.model_cr
#     def init(self):
#         tools.drop_view_if_exists(self.env.cr, self._table)
#         self.env.cr.execute("""CREATE or REPLACE VIEW widget_doanh_so as (
#             select min(so.id) as id,
#             so.confirmation_date as date_order,
#             sum(CASE WHEN so.sale_order_return = FALSE THEN so.amount_untaxed + so.amount_tax ELSE -so.amount_total END) AS amount_total
#             from sale_order so
#             WHERE so.state in ('sale')
#             GROUP BY so.confirmation_date)""")
#
#     def get_date_text(self, date):
#         thu = {
#             '0': 'CN',
#             '1': 'Thứ 2',
#             '2': 'Thứ 3',
#             '3': 'Thứ 4',
#             '4': 'Thứ 5',
#             '5': 'Thứ 6',
#             '6': 'Thứ 7',
#         }
#         day = '%d %b %Y'
#         date_list = datetime.strptime(date, day)
#         thu_date = thu.get(date_list.strftime('%w'),False)
#         return thu_date + " " +date_list.strftime('%d/%m')
#
#     def get_month_text(self, month):
#         if 'tháng' in month:
#             try:
#                 month = month.split(' ')
#                 return "Th " + month[1]
#             except:
#                 return month
#         else:
#             thang = {
#                 'January': '01',
#                 'February': '02',
#                 'March': '03',
#                 'April': '04',
#                 'May': '05',
#                 'June': '06',
#                 'July': '07',
#                 'August': '08',
#                 'September': '09',
#                 'October': '10',
#                 'November': '11',
#                 'December': '12'
#             }
#             month = month.split(' ')[0]
#             return "Th " + thang.get(month,False)
#
#     @api.model
#     def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
#         if self._context.get('doanh_so_base_date', False):
#             datetime_now = datetime.now()
#             day_now = int(datetime_now.strftime('%w'))
#             start_date = (datetime_now + timedelta(days=-(day_now + 1))).strftime('%Y-%m-%d 17:00:00')
#             end_date = (datetime_now + timedelta(days=(6 - day_now))).strftime('%Y-%m-%d 17:00:00')
#             domain = ['&', ('date_order', '>=', start_date), ('date_order', '<', end_date)]
#         if self._context.get('doanh_so_base_week',False):
#             datetime_now = datetime.now()
#             start_date = (datetime_now + timedelta(weeks=-6)).strftime('%Y-%m-%d 17:00:00')
#             end_date = datetime_now.strftime('%Y-%m-%d 17:00:00')
#             domain = ['&', ('date_order', '>=', start_date), ('date_order', '<', end_date)]
#         if self._context.get('doanh_so_base_month',False):
#             datetime_now = datetime.now()
#             start_date = (datetime_now + timedelta(weeks=-14)).strftime('%Y-%m-%d 17:00:00')
#             end_date = datetime_now.strftime('%Y-%m-%d 17:00:00')
#             domain = ['&', ('date_order', '>=', start_date), ('date_order', '<', end_date)]
#
#         res = super(widget_doanh_so, self).read_group(domain, fields, groupby, offset=offset,
#                                                  limit=limit, orderby=orderby, lazy=lazy)
#         if self._context.get('doanh_so_base_date',False):
#             new_res = []
#             for count in range(0, 7):
#                 date_current_order = (datetime_now + timedelta(days=-(day_now + 1))) + timedelta(days=count)
#                 date_order = (date_current_order + timedelta(days=1)).strftime('%d %b %Y')
#                 check_exist = False
#                 for list in res:
#                     date = list.get('date_order:day', False)
#                     if date == date_order:
#                         new_res.append(list)
#                         check_exist = True
#                 if not check_exist:
#                     start_date = date_current_order.strftime('%Y-%m-%d 17:00:00')
#                     end_date = (date_current_order + timedelta(days=1)).strftime('%Y-%m-%d 17:00:00')
#                     new_res.append({
#                         '__count': 0L,
#                         'date_order:day': date_order,
#                         '__domain': ['&', ('date_order', '>=', start_date), ('date_order', '<', end_date)],
#                         'amount_total': 0
#                     })
#
#             for list in new_res:
#                 date = list.get('date_order:day', False)
#                 list.update({
#                     'date_order:day': self.get_date_text(date),
#                     'amount_total': int(list.get('amount_total', 0) / 1000000)
#                 })
#             res = new_res
#             res.reverse()
#
#         if self._context.get('doanh_so_base_week',False):
#             res = res[-4:]
#             res.reverse()
#             for list in res:
#                 week = list.get('date_order:week', False)
#                 week = week.split(' ')[0].replace('W','Wk ')
#                 list.update({
#                     'date_order:week': week,
#                     'amount_total' : int(list.get('amount_total',0) / 1000000)
#                 })
#         if self._context.get('doanh_so_base_month',False):
#             res = res[-3:]
#             res.reverse()
#             for list in res:
#                 month = list.get('date_order:month', False)
#                 list.update({
#                     'date_order:month': self.get_month_text(month),
#                     'amount_total': int(list.get('amount_total',0) / 1000000)
#                 })
#
#         return res
#
#
