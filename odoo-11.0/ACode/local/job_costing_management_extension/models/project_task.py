from odoo import models, fields

class Sub_Contractor(models.Model):
    _inherit = 'project.task'

    sub_contractor = fields.Many2one(comodel_name='res.partner', string="Sub Contractor",)

    