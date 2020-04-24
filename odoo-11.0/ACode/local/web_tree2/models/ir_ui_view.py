# -*- coding: utf-8 -*-

from odoo import models, fields, api

_TREE2_TUP = [('tree2', "Tree2")]


class View(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=_TREE2_TUP)