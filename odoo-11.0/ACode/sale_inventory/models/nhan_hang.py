# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class stock_picking_ihr(models.Model):
    _inherit = 'stock.picking'

    receiver = fields.Many2one('res.users', 'Nhân viên nhận hàng', required=True)
    receive_increase = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Nhận hàng tăng cường', default='no',
                                        required=True)
    move_type = fields.Selection([
        ('direct', 'Partial'),
        ('one', 'All at once')], string='Delivery Type', default='direct',
        required=True)
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=True)
    location_id = fields.Many2one('stock.location', string='Source Location Zone')
    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location Zone',
        readonly=True, required=True,
        states={'draft': [('readonly', False)], 'confirmed': [('readonly', True)]})
    receive_method = fields.Selection(
        [('warehouse', 'Nhận hàng trả lại tại kho'),
         ('local', 'Nhận hàng trả lại tại địa chỉ giao hàng')], string='Phương thức nhận hàng')

    date_base_order = fields.Date(string='Ngày đặt hàng')
    # time_accept = fields.Datetime(string='Thời điểm xác nhận', readonly=True)
    min_date = fields.Datetime(string='Ngày giao hàng')
    # origin_sub = fields.Char(string='Source Document')
    kho_luu_tru = fields.Selection([('normal', 'Kho bình thường'), ('error', 'Hàng Lỗi')], string='Kho lưu trữ',
                                   default='normal')
    sale_id = fields.Char(string='Sale Order', required=True)
    user_sale_id = fields.Many2one('res.users', string='Nhân viên bán hàng', required=True)
    reason_cancel = fields.Many2one('ly.do.tra.hang', string='Nguyên nhân trả hàng')
    user_create_return = fields.Many2one('res.users', string='Nhân viên tạo trả hàng')
    picking_note = fields.Char(string='Ghi chú')

    # receipt_state = fields.Selection(
    #     [('draft', 'Bản thảo'), ('reveive', 'Nhận hàng'), ('done', 'Hoàn thành'), ('cancel', 'Cancel')],
    #     default='draft')

    # qty = fields.Float(compute='_get_total_quantity')
    #
    # @api.depends('order_line.product_uom_qty')
    # def _get_total_quantity(self):
    #     for rec in self:
    #         total_quantity = 0
    #         for line in rec.move_lines:
    #             total_quantity += line.product_uom_qty
    #         rec.qty = total_quantity

    # @api.multi
    # def name_get(self):
    #     res = []
    #     for record in self:
    #         res.append((record.id, "TTS/PICK/00%s" % (record.name)))
    #     return res
