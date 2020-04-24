# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ir_exports_line(models.Model):
    _inherit = 'ir.exports.line'

    @api.multi
    def unlink(self):
        res = super(ir_exports_line, self).unlink()
        return res

class ir_exports(models.Model):
    _inherit = 'ir.exports'

    @api.multi
    def unlink(self):
        if self.create_uid and self.create_uid.name == unicode('Nguyễn Thị Yến Nga', "utf-8"):
            raise UserError(_("You can not delete it."))
        res = super(ir_exports_line, self).unlink()
        return res

