# -*- coding: utf-8 -*-

from odoo import models, fields, api

class vieterp_stock(models.Model):
    _inherit = 'stock.picking'

    receiver = fields.Many2one('hr.employee', 'Receiver')
    shipper = fields.Many2one('hr.employee', 'Shipper')
    create_uid = fields.Many2one('res.users', 'Created', default=lambda self: self.env.uid)
    approval = fields.Many2one('hr.employee', 'Approval')

    done_date = fields.Datetime('Done Date')

    @api.multi
    def do_transfer(self):
        result = super(vieterp_stock, self).do_transfer()
        for record in self:
            record.done_date = fields.Datetime.now()
        return result