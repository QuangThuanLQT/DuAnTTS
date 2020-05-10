
from datetime import datetime
from odoo import models, fields

class Job_Cost_line(models.Model):
    _inherit = 'job.cost.line'

    date = fields.Date(string='Date',required=True,copy=False, default=datetime.today())