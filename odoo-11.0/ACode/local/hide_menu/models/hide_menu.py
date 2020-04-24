# -*- coding: utf-8 -*-

from openerp import api, models, fields
from datetime import datetime,timedelta ,date
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class ir_ui_menu(models.Model):
    _inherit = 'ir.ui.menu'
    
    active = fields.Boolean('Active', default=True)
        

