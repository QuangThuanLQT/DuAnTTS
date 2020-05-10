from odoo import models, fields, api
from datetime import datetime
from lxml import etree



class respartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def default_get(self, fields):
        res = super(respartner, self).default_get(fields)
        if self._context and 'default_bank_id' in self._context:
            res['bank'] = True
        return res