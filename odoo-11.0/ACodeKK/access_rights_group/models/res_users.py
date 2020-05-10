from odoo import api, fields, models, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    access_rights_id = fields.Many2one('access.rights.group', string="Access Rights Group")

    @api.multi
    def set_groups(self,values):
        if values.get('access_rights_id'):
            group_obj = self.env['access.rights.group'].browse(values.get('access_rights_id'))
            values['groups_id'] = [(6,0,group_obj.group_ids.ids)]
        return values

    @api.model
    def create(self, values):
        values = self.set_groups(values)
        return super(ResUsers, self).create(values)

    @api.multi
    def write(self, values):
        values = self.set_groups(values)
        return super(ResUsers, self).write(values)

ResUsers()