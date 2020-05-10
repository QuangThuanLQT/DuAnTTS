# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ProjectTaskTemplate(models.Model):

    _name = 'project.task.template'
    _inherit = 'project.task'

    use_as_template = fields.Boolean(
        string="Active",
        default=True,
        help="Set to use this template.",
    )
    default_stage_id = fields.Many2one(
        'project.task.type',
        string="Default Stage",
        help="Created task will be put selected stage.",
    )

    @api.multi
    def toggle_template(self):
        """ Inverse the value of the field ``use_as_template`` on the records in ``self``. """
        for record in self:
            record.use_as_template = not record.use_as_template


class ProjectProject(models.Model):

    _inherit = 'project.project'

    @api.model
    def create(self, vals):
        res = super(ProjectProject, self).create(vals)
        templates = self.env['project.task.template'].search([
            ('use_as_template', '=', True),
        ])
        ProjectTask = self.env['project.task']
        for template in templates:
            vals = {}
            fields_data = template.fields_get()
            skip_fields = (
                'project_id',
                'message_follower_ids',
                'id',
                'write_date',
                'create_data',
                'use_as_template',
                'message_ids',
                'default_stage_id',
            )
            for field_data in fields_data:
                if field_data not in skip_fields:
                    value = template.__getattribute__(field_data)
                    if fields_data[field_data]['type'] == 'one2many':
                        vals[field_data] = value.mapped('id')
                    elif fields_data[field_data]['type'] == 'many2one':
                        vals[field_data] = value.id
                    elif fields_data[field_data]['type'] == 'many2many':
                        vals[field_data] = [[6, 0, value.mapped('id')]]
                    else:
                        vals[field_data] = value
            vals.update({
                'stage_id': template.default_stage_id.id,
                'project_id': res.id,
            })
            ProjectTask.create(vals)
        return res
