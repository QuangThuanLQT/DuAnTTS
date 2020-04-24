from odoo import api, fields, models, _

class AccessRightsGroup(models.Model):
    _name = 'access.rights.group'
    _inherit = ['mail.thread']
    _description = 'Access Rights Group'
    _order = 'id desc'

    name = fields.Char(track_visibility='onchange', string='Group Name')
    group_ids = fields.Many2many('res.groups', track_visibility='onchange', string='Groups')
    
    @api.multi
    def write(self, vals):
        res = super(AccessRightsGroup, self).write(vals)
        if 'group_ids' in vals:
            user_ids = self.env['res.users'].search([('access_rights_id','=',self.id)])
            if user_ids:
                for user in user_ids:
                    user.write({'access_rights_id': self.id})
        return res
    

AccessRightsGroup()