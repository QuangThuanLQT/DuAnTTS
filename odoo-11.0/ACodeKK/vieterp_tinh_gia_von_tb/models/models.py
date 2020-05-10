# -*- coding: utf-8 -*-

from odoo import models, fields, api

class vieterp_tinh_gia_von_tb(models.Model):
    _name = "tinh.gia.von.tb"

    start_date = fields.Date(String='Start Date', required=True)
    end_date = fields.Date(String='End Date')

