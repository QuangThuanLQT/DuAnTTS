# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
import StringIO
import xlsxwriter
import pytz
from datetime import datetime
from datetime import date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class res_partner(models.Model):
    _inherit = 'res.partner'

    count_product_interest = fields.Integer(compute='get_product_interest')

    @api.multi
    def get_product_interest(self):
        for rec in self:
            product_interest_ids = self.env['product.interest'].search([('partner_id', '=', rec.id)])
            rec.count_product_interest = len(product_interest_ids)

    @api.multi
    def action_view_product_interest(self):
        action = self.env.ref('tts_product_interest.product_interest_action').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        return action