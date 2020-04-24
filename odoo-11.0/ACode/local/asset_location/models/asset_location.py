# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class asset_location(models.Model):
    _name = 'asset.location'


    name = fields.Char('Name', required=1)
    account_asset_asset_ids = fields.One2many('account.asset.asset', 'asset_location_id')
