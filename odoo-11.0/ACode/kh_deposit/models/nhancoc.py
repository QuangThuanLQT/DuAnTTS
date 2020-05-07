# -*- coding: utf-8 -*-

from odoo import models, fields, api


class nhancoc(models.Model):
    _inherit = 'res.partner'

    dat_coc = fields.Float('Đặt cọc', digits=(16, 2))
    sale_amount = fields.Float('Tổng bán')
    return_amount = fields.Float('Tổng trả hàng')
    sale_total_amount = fields.Float('Tổng bán trừ tổng trả hàng')


    # def _compute_sale_total_amount(self):
    #     for record in self:
    #         sale_amount = return_amount = 0
    #         sale_ids = self.env['sale.order'].search(
    #             [('partner_id', '=', record.id), ('sale_order_return', '=', False)]).filtered(
    #             lambda s: s.trang_thai_dh == 'done')
    #         for order in sale_ids:
    #             sale_amount += order.amount_total
    #         sale_return_ids = self.env['sale.order'].search(
    #             [('partner_id', '=', record.id), ('sale_order_return', '=', True)]).filtered(
    #             lambda s: s.trang_thai_dh == 'done')
    #         for order_return in sale_return_ids:
    #             return_amount += order_return.amount_total
    #         # code for Vendors
    #         purchase_ids = self.env['purchase.order'].search(
    #             [('partner_id', '=', record.id), ('purchase_order_return', '=', False)]).filtered(
    #             lambda s: s.operation_state == 'done')
    #         for purchase in purchase_ids:
    #             sale_amount += purchase.amount_total
    #         purchase_return_ids = self.env['purchase.order'].search(
    #             [('partner_id', '=', record.id), ('purchase_order_return', '=', True)]).filtered(
    #             lambda s: s.operation_state == 'done')
    #         for purchase_return in purchase_return_ids:
    #             return_amount += purchase_return.amount_total
    #
    #         record.sale_total_amount = sale_amount - return_amount
    #         record.sale_amount = sale_amount
    #         record.return_amount = return_amount



