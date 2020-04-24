# -*- coding: utf-8 -*-

from odoo import models, fields, api


class sale_orer_ihr(models.Model):
    _inherit = 'sale.order'

    so_tien_da_thu = fields.Float(string='Số tiền đã thu', required=0, copy=False)
    con_phai_thu = fields.Float(string='Số tiền còn phải thu', required=1, compute='_con_phai_thu')
    trang_thai_tt = fields.Selection(
        [('chua_tt', 'Chưa thanh toán'),
         ('tt_1_phan', 'Thanh toán 1 phần'),
         ('done_tt', 'Hoàn tất thanh toán')],
        string='Trạng thái thanh toán', default='chua_tt', required=1, copy=False)

    # @api.model
    # def create(self,val):
    #     res = super(sale_orer_ihr, self).create(val)
    #     res.so_tien_con_phai_thu = res.amount_total
    #     return res

    @api.multi
    def write(self, val):
        res = super(sale_orer_ihr, self).write(val)
        if not self._context.get('not_run', False):
            for rec in self:
                if val.get('amount_total',False):
                    if rec.so_tien_da_thu and rec.so_tien_da_thu < val.get('amount_total',False):
                        rec.with_context({'not_run': True}).write({
                            'trang_thai_tt': 'tt_1_phan'
                        })
        return res


    @api.multi
    def _con_phai_thu(self):
        for rec in self:
            rec.con_phai_thu = rec.amount_total - rec.so_tien_da_thu
