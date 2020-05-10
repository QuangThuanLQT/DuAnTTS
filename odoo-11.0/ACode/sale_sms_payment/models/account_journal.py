# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class account_khoan_thu_khac(models.Model):
    _inherit = 'account.journal'

    bank_name = fields.Char('Long Code')