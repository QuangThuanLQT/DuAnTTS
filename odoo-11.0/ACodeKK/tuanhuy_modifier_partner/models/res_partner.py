# -*- coding: utf-8 -*-

from odoo import models, fields, api

class res_partner_inherit(models.Model):
    _inherit = 'res.partner'

    group_kh1_id = fields.Many2one('partner.group.hk1',string="Group Customer 1")
    group_kh2_id = fields.Many2one('partner.group.hk2', string="Group Customer 2")

    # def _check_duplicate_name(self):
    #     res = True
    #     if self.env['res.partner'].search([('id', '!=', self.id), ('name', '=', self.name)]):
    #         res = False
    #     return res
    #
    # _constraints = [(_check_duplicate_name, 'Tên khách hàng đã tồn tại.', ['name'])]

    @api.constrains("vat")
    def check_vat(self):
        pass


class partner_group_kh1(models.Model):
    _name = 'partner.group.hk1'

    name = fields.Char(string='Group Name')


class partner_group_kh2(models.Model):
    _name = 'partner.group.hk2'

    name = fields.Char(string='Group Name')