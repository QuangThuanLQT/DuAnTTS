# -*- coding: utf-8 -*-
from openerp import api, fields, models

class OrderingTime(models.Model):
    _name = 'ordering.time'
    
    day = fields.Char("Day")
    sequence = fields.Integer("Sequence")
    start_time = fields.Float("Start Time")
    end_time = fields.Float("End Time")