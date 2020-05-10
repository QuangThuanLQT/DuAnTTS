# -*- encoding: utf-8 -*-
##############################################################################
#
#    General Solutions, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://gscom.vn>). All Rights Reserved
#
##############################################################################
from dateutil import relativedelta
import time
from datetime import datetime
from datetime import timedelta
from odoo import models, fields, api

import locale
import sys

locale.setlocale(locale.LC_ALL, '')
reload(sys)
sys.setdefaultencoding('utf8')

class vieterp_report_cost(models.TransientModel):
    _name = 'vieterp.report.cost'

    # @api.model
    # def _get_default_context(self):
    #     sale_ids   = self.env.context.get('active_ids')
    #     if sale_ids:

    @api.model
    def default_get(self, fields):
        res = super(vieterp_report_cost, self).default_get(fields)
        sale_id = self.env.context.get('active_id')
        sale    = self.env['account.asset.asset'].browse(sale_id)
        if 'context' in fields:
            res.update({'context': 'ABC'})
        return res

    context = fields.Html('Contents', help='Automatically sanitized HTML contents', default='_get_default_context')