# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class LiabilitiesTime(models.Model):
    _name = 'liabilities.time'

    name = fields.Char()