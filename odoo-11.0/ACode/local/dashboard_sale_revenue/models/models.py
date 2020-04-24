# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import pytz
from calendar import monthrange


class dashboard_sale_revenue(models.Model):
    _name = 'dashboard.sale.revenue'

    name = fields.Char("")

    def cover_datetime(self, date):
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        resuft = datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT)
        resuft = pytz.utc.localize(resuft).astimezone(user_tz).strftime(
            '%d/%m/%Y %H:%M:%S')
        return resuft

    def get_string_with_width(self, string, width):
        if len(string) > width:
            return string[0:width] + "..."
        else:
            return string

    def get_cancel_date(self, order):

        sql = """SELECT mtv.create_date FROM mail_tracking_value mtv 
                LEFT JOIN mail_message mm ON (mtv.mail_message_id = mm.id)
                WHERE mtv.field = 'state' AND mtv.new_value_char in ('Cancelled', 'Đã hủy') 
                AND mm.res_id = %s and model = %s 
                ORDER BY mtv.create_date DESC
                """
        params = (order.id, 'sale.order')
        self.env.cr.execute(sql, params)
        result = self.env.cr.dictfetchall()
        if result:
            return result[0].get('create_date')
        return False

    @api.model
    def get_sale_order_data(self):
        datetime_now = datetime.now()
        total_quotaion = total_sale_waiting_phieu_thu = total_sale_ready = total_sale_done = 0
        start_current_month = datetime_now + timedelta(days=-(datetime_now.day - 1))
        start_date = start_current_month.strftime('%Y-%m-%d 17:00:00')
        days_in_month = monthrange(start_current_month.year, start_current_month.month)[1]
        end_date = (start_current_month + timedelta(days=days_in_month - 1)).strftime('%Y-%m-%d 17:00:00')
        employee_ceo = self.env['hr.employee'].search([('job_id.name', '=', 'CEO')])
        if self._uid in employee_ceo.mapped('user_id').ids:
            domain = [('confirmation_date', '>=', start_date),
                      ('confirmation_date', '<', end_date),
                      ('trang_thai_dh', '!=', 'cancel'),
                      ]
        else:
            domain = [('user_id', '=', self._uid), ('confirmation_date', '>=', start_date), ('trang_thai_dh', '!=', 'cancel'),
                      ('confirmation_date', '<', end_date)]
        sale_order_raw = self.env['sale.order'].search(domain)
        sale_order = self.env['sale.order'].search(
            [('state', '=', 'sale'), ('sale_order_return', '=', False), ('id', 'in', sale_order_raw.ids)])
        sale_order_return = self.env['sale.order'].search(
            [('state', '=', 'sale'), ('sale_order_return', '=', True), ('id', 'in', sale_order_raw.ids)])
        doanh_so_trong_thang = 0
        gia_tri_tb_thang = 0
        sl_kh_mua_thang = 0
        sl_new_kh_mua_hang = 0
        if sale_order:
            doanh_so_trong_thang = sum(sale_order.mapped('amount_untaxed')) + sum(
                sale_order.mapped('amount_tax')) - sum(sale_order_return.mapped('amount_total'))
            gia_tri_tb_thang = (sum(sale_order.mapped('amount_untaxed')) + sum(sale_order.mapped('amount_tax'))) / len(
                sale_order)
            sl_kh_mua_thang = len(sale_order.mapped('partner_id'))
            sl_new_kh_mua_hang = self.env['res.partner'].search([
                ('id', 'in', sale_order.mapped('partner_id').ids),
                ('create_date', '>=', start_date),
                ('create_date', '<=', end_date),
            ])
            sl_new_kh_mua_hang = len(sl_new_kh_mua_hang)

        if self._uid in employee_ceo.mapped('user_id').ids:
            quotation_ids = self.env['sale.order'].search(
                [('state', 'in', ('draft', 'sent', 'cancel')), ('sale_order_return', '=', False), ('sale_set_draft_id', '=', False)])
        else:
            quotation_ids = self.env['sale.order'].search(
                [('user_id', '=', self._uid), ('state', 'in', ('draft', 'sent', 'cancel')),
                 ('sale_order_return', '=', False), ('sale_set_draft_id', '=', False)])
        state = dict(self.env['sale.order'].fields_get(allfields=['state'])['state']['selection'])
        quotation_list = []
        for quotation_id in quotation_ids:
            if quotation_id.state == 'cancel':
                state_cancel_date = self.get_cancel_date(quotation_id)
                if state_cancel_date:
                    time_cancel = (datetime_now - datetime.strptime(state_cancel_date, '%Y-%m-%d %H:%M:%S.%f')).days
                    if time_cancel > 0:
                        continue
            if quotation_id.state != 'cancel':
                total_quotaion += quotation_id.amount_total
            quotation_list.append({
                'id': quotation_id.id,
                'name': quotation_id.name,
                'confirmation_date': self.cover_datetime(quotation_id.confirmation_date),
                'partner_id': self.get_string_with_width(quotation_id.partner_id.display_name, 52) or '',
                'note': self.get_string_with_width(quotation_id.note, 114) if quotation_id.note else '',
                'state': state.get(quotation_id.state) if quotation_id.state else '',
                'amount_total': "%s đ" % ('{:,}'.format(int(quotation_id.amount_total))),
                'state_value': quotation_id.state,
            })

        if self._uid in employee_ceo.mapped('user_id').ids:
            sale_waiting_phieu_thu_ids = self.env['sale.order'].search(
                [('trang_thai_dh', 'in', ['waiting_pick']),
                 ('sale_order_return', '=', False), ('sale_set_draft_id', '=', False)])
        else:
            sale_waiting_phieu_thu_ids = self.env['sale.order'].search(
                [('user_id', '=', self._uid), ('trang_thai_dh', 'in', ['waiting_pick']),
                 ('sale_order_return', '=', False), ('sale_set_draft_id', '=', False)])
        sale_waiting_phieu_thu_list = []
        for sale_id in sale_waiting_phieu_thu_ids:
            if sale_id.state == 'cancel':
                state_cancel_date = self.get_cancel_date(sale_id)
                if state_cancel_date:
                    time_cancel = (datetime_now - datetime.strptime(state_cancel_date, '%Y-%m-%d %H:%M:%S.%f')).days
                    if time_cancel > 0:
                        continue
            sale_waiting_phieu_thu_list.append({
                'id': sale_id.id,
                'name': sale_id.name,
                'confirmation_date': self.cover_datetime(sale_id.confirmation_date),
                'partner_id': self.get_string_with_width(sale_id.partner_id.display_name, 52) or '',
                'note': self.get_string_with_width(sale_id.note, 114) if sale_id.note else '',
                'amount_total': "%s đ" % ('{:,}'.format(int(sale_id.amount_total))),
                'con_phai_thu': "%s đ" % ('{:,}'.format(int(sale_id.con_phai_thu))),
                'so_tien_da_thu': "%s đ" % ('{:,}'.format(int(sale_id.so_tien_da_thu))),
                'state': sale_id.state
            })

        if self._uid in employee_ceo.mapped('user_id').ids:
            sale_ready_ids = self.env['sale.order'].search(
                [('trang_thai_dh', 'in', (
                    'ready_pick', 'picking', 'waiting_pack', 'packing', 'waiting_delivery', 'delivery')),
                 ('sale_order_return', '=', False)])
        else:
            sale_ready_ids = self.env['sale.order'].search(
                [('user_id', '=', self._uid), ('trang_thai_dh', 'in', (
                    'ready_pick', 'picking', 'waiting_pack', 'packing', 'waiting_delivery', 'delivery')),
                 ('sale_order_return', '=', False)])
        sale_ready_list = []
        for sale_id in sale_ready_ids:
            if sale_id.state == 'cancel':
                state_cancel_date = self.get_cancel_date(sale_id)
                if state_cancel_date:
                    time_cancel = (datetime_now - datetime.strptime(state_cancel_date, '%Y-%m-%d %H:%M:%S.%f')).days
                    if time_cancel > 0:
                        continue
            sale_ready_list.append({
                'id': sale_id.id,
                'name': sale_id.name,
                'confirmation_date': self.cover_datetime(sale_id.confirmation_date),
                'partner_id': self.get_string_with_width(sale_id.partner_id.display_name, 52) or '',
                'note': self.get_string_with_width(sale_id.note, 114) if sale_id.note else '',
                'amount_total': "%s đ" % ('{:,}'.format(int(sale_id.amount_total))),
                'trang_thai_tt': dict(sale_id.fields_get(['trang_thai_tt'])['trang_thai_tt']['selection'])[
                    sale_id.trang_thai_tt] if sale_id.trang_thai_tt else '',
                'trang_thai_dh': dict(sale_id.fields_get(['trang_thai_dh'])['trang_thai_dh']['selection'])[
                    sale_id.trang_thai_dh] if sale_id.trang_thai_dh else '',
            })

        if self._uid in employee_ceo.mapped('user_id').ids:
            sale_done_ids = self.env['sale.order'].search(
                [('trang_thai_dh', '=', 'done'), ('sale_order_return', '=', False),
                 ('con_phai_thu_store', '>', 1)])
        else:
            sale_done_ids = self.env['sale.order'].search(
                [('user_id', '=', self._uid), ('trang_thai_dh', '=', 'done'), ('sale_order_return', '=', False),
                 ('con_phai_thu_store', '>', 1)])
        sale_done_list = []
        for sale_id in sale_done_ids:
            sale_done_list.append({
                'id': sale_id.id,
                'name': sale_id.name,
                'confirmation_date': self.cover_datetime(sale_id.confirmation_date),
                'partner_id': self.get_string_with_width(sale_id.partner_id.display_name, 52) or '',
                'note': self.get_string_with_width(sale_id.note, 114) if sale_id.note else '',
                'amount_total': "%s đ" % ('{:,}'.format(int(sale_id.amount_total))),
                'con_phai_thu': "%s đ" % ('{:,}'.format(int(sale_id.con_phai_thu))),
                'so_tien_da_thu': "%s đ" % ('{:,}'.format(int(sale_id.so_tien_da_thu))),
            })

        return [{
            'doanh_so_trong_thang': "%s đ" % ('{:,}'.format(int(doanh_so_trong_thang))),
            'tong_don_ban': len(sale_order),
            'tong_don_tra': len(sale_order_return),
            'gia_tri_tb_thang': "%s đ" % ('{:,}'.format(int(gia_tri_tb_thang))),
            'sl_kh_mua_thang': sl_kh_mua_thang,
            'sl_new_kh_mua_hang': sl_new_kh_mua_hang,
            'quotation_list': quotation_list,
            'total_quotaion': "%s đ" % ('{:,}'.format(int(total_quotaion))),
            'sale_waiting_phieu_thu_list': sale_waiting_phieu_thu_list,
            'total_sale_waiting_phieu_thu': "%s đ" % (
                '{:,}'.format(int(sum(sale_waiting_phieu_thu_ids.mapped('amount_total'))))),
            'sale_ready_list': sale_ready_list,
            'total_sale_ready': "%s đ" % ('{:,}'.format(int(sum(sale_ready_ids.mapped('amount_total'))))),
            'sale_done_list': sale_done_list,
            'total_sale_done': "%s đ" % ('{:,}'.format(int(sum(sale_done_ids.mapped('amount_total'))))),
        }]

    @api.model
    def get_action_id(self, action_id):
        action = self.env.ref('dashboard_sale_revenue.action_sale_dashboard').id
        if action == int(action_id):
            return True
        return False
