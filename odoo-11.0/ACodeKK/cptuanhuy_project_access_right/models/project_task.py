# -*- coding: utf-8 -*-

from odoo import models, fields, api

class project_task_inherit(models.Model):
    _inherit = 'project.task'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self.env.user.has_group('cptuanhuy_project_access_right.group_only_see_task_assign'):
            task_list = []
            task_ids = self.search([])
            for task_id in task_ids:
                if self._uid == task_id.user_id.id:
                    task_list.append(task_id.id)
            domain.append(('id', 'in', task_list))
        res = super(project_task_inherit, self).search_read(domain=domain, fields=fields, offset=offset,
                                                    limit=limit, order=order)
        return res