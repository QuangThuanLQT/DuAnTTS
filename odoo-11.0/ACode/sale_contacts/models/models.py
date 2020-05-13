# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Contact_Tags(models.Model):
    _inherit = 'res.partner.category'


class Contact_Titles(models.Model):
    _inherit = 'res.partner.title'


class Countries(models.Model):
    _inherit = 'res.country'


class Fed_States(models.Model):
    _inherit = 'res.country.state'


class Country_Group(models.Model):
    _inherit = 'res.country.group'


class Banks(models.Model):
    _inherit = 'res.bank'


class Bank_Accounts(models.Model):
    _inherit = 'res.partner.bank'


class Partner_Level(models.Model):
    _inherit = 'res.partner.grade'


class Partner_Activations(models.Model):
    _inherit = 'res.partner.activation'


class Stages(models.Model):
    _inherit = 'crm.stage'


class Lead_Tags(models.Model):
    _inherit = 'crm.lead.tag'


class Lost_Reasons(models.Model):
    _inherit = 'crm.lost.reason'


class Activity_Types(models.Model):
    _inherit = 'mail.activity.type'
