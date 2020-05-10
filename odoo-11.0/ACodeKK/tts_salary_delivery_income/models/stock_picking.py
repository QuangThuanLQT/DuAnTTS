from odoo import models, fields, api
from datetime import datetime

class _stock_picking_inherit(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def delivery_action_do_new_transfer(self):
        res = super(_stock_picking_inherit, self).delivery_action_do_new_transfer()
        phuong_thuc_giao_hang = self.delivery_method
        if phuong_thuc_giao_hang != 'warehouse':
            code = 'SKL' + str(int(self.user_delivery_id.id)) + '/' + datetime.now().strftime("%m%y")
            value = self.env['salary.delivery.income'].search([('default_code', '=', code)])
            tn = 0
            if self.giao_hang_tang_cuong == 'no':
                sl_gh_bt = self.kich_thuoc_don_hang.number_sign
                sl_gh_tc = 0
                thuong_giao_hang = self.env['tts.delivery.scope'].search([('phuong_xa', '=', self.ward_id.name), ('feosco_district_id', '=', self.district_id.name)]).thuong_giao_hang
            else:
                sl_gh_bt = 0
                sl_gh_tc = self.kich_thuoc_don_hang.number_sign
                thuong_giao_hang = self.env['tts.delivery.scope'].search([('phuong_xa', '=', self.ward_id.name), ('feosco_district_id', '=', self.district_id.name)]).thuong_giao_hang_tang_ca
            if thuong_giao_hang:
                tn = self.kich_thuoc_don_hang.number_sign * thuong_giao_hang
                if tn:
                    value_tn = self.env['income.inventory'].search([('source_sale_id', '=', self.origin)]).write({
                        'thu_nhap': tn,
                    })

            if not value:
                value = self.env['salary.delivery.income'].create({
                    'default_code': code,
                    'month': datetime.now().strftime("%m/%Y"),
                    'name': self.user_delivery_id.name,
                    'sl_gh_bt': sl_gh_bt,
                    'sl_gh_tc': sl_gh_tc,
                    'thu_nhap': tn,
                    'thang': datetime.now().strftime("%m"),
                    'nam': datetime.now().strftime("%Y"),
                })
            else:
                if self.giao_hang_tang_cuong == 'no':
                    sl_gh_bt = value.sl_gh_bt
                    sl_gh_bt += self.kich_thuoc_don_hang.number_sign
                    thu_nhap = value.thu_nhap + tn
                    value.write({
                        'sl_gh_bt': sl_gh_bt,
                        'thu_nhap': thu_nhap,
                    })
                else:
                    sl_gh_tc = value.sl_gh_tc
                    sl_gh_tc += self.kich_thuoc_don_hang.number_sign
                    thu_nhap = value.thu_nhap + tn
                    value.write({
                        'sl_gh_tc': sl_gh_tc,
                        'thu_nhap': thu_nhap,
                    })
        return res

