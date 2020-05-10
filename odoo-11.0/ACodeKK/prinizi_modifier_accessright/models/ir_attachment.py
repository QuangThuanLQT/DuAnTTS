# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ir_attachment_ihr(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self.env.user.has_group('prinizi_modifier_accessright.group_nv_kho') or \
            self.env.user.has_group('tts_modifier_access_right.group_ql_kho'):
            return super(ir_attachment_ihr, self.sudo())._search(args, offset=offset, limit=limit, order=order,
                                                    count=count, access_rights_uid=access_rights_uid)
        else:
            return super(ir_attachment_ihr, self)._search(args, offset=offset, limit=limit, order=order,
                                                                 count=count, access_rights_uid=access_rights_uid)