# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    user_logged = fields.Boolean(
        string="User Logged",
        default=True,
        help=_("If checked, "
               "the menu will be displayed when the user is logged.")
    )

    user_not_logged = fields.Boolean(
        string="User Not Logged",
        default=True,
        help=_("If checked, "
               "the menu will be displayed when the user is not logged.")
    )