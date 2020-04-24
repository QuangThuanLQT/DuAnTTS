# -*- coding: utf-8 -*-
from odoo import models, fields, api
import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import pytz

class confirm_picking_popup(models.Model):
    _name = 'confirm.picking.popup'

    date_start      = fields.Date('Ngày bắt đầu',required=True)
    date_end        = fields.Date('Ngày kết thúc')
    # state           = fields.Selection([('all','Chưa hoàn thành'),('draft','Bản thảo'),('waiting','Chờ hoạt động khác'),('confirmed','Chờ có hàng'),('partially_available','Giao Một Phần'),('assigned','Có sẵn')],default='all')
    picking_ids     = fields.Many2many('stock.picking',string="Các dịch chuyển")
    picking_sub_ids = fields.Many2many('stock.picking','confirm_picking_popup_picking_sub_rel','picking_id','popup_id',string="Các dịch chuyển")

    @api.onchange('date_start','date_end')
    def onchange_get_picking_ids(self):
        if self.date_start and self.date_end:
            datetime_start = self.convert_to_utc(self.date_start)
            datetime_end = self.convert_to_utc(self.date_end)
            domain = [('min_date','>=',datetime_start),('min_date','<=',datetime_end),('state','not in',['cancel','done'])]
            picking_ids = self.env['stock.picking'].search(domain)
            self.picking_ids = picking_ids
            self.picking_sub_ids = picking_ids

    @api.onchange('picking_sub_ids')
    def onchange_picking_sub_ids(self):
        if self.picking_sub_ids:
            self.picking_ids = self.picking_sub_ids

    @api.multi
    def confirm_picking(self):
        if self.picking_ids:
            self.picking_ids.write({'need_to_confirm': True})

    def convert_to_utc(self, date):
        timezone_tz = 'Asia/Ho_Chi_Minh'
        if self.env.user and self.env.user.tz:
            timezone_tz = self.env.user.tz
        else:
            timezone_tz = 'Asia/Ho_Chi_Minh'
        date_from = datetime.datetime.strptime(date,DEFAULT_SERVER_DATE_FORMAT).replace(tzinfo=pytz.timezone(timezone_tz)).astimezone(pytz.utc)
        return date_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

