# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class account_asset_asset(models.Model):
    _inherit = 'account.asset.asset'

    asset_location_id = fields.Many2one('asset.location', 'Current Location')