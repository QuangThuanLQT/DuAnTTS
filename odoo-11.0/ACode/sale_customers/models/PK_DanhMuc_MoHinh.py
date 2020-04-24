# -*- coding: utf-8 -*-

from odoo import models, fields, api


class partner_group_kh1(models.Model):
    _name = 'partner.group.hk1'

    name = fields.Char(string='Group Name')


class partner_group_kh2(models.Model):
    _name = 'partner.group.hk2'

    name = fields.Char(string='Group Name')