# -*- coding: utf-8 -*-
from odoo.tests import common


class TestProject(common.SingleTransactionCase):

    def test_task_create_from_template(self):
        ProjectTask = self.env['project.task']
        project = self.env['project.project'].create({
            'name': "Test Project for Template Testing",
        })
        template1 = self.browse_ref(
            'project_task_template.project_task_template_1')
        task1 = ProjectTask.search([
            ('project_id', '=', project.id),
            ('user_id', '=', template1.user_id.id),
            ('partner_id', '=', template1.partner_id.id),
            ('date_deadline', '=', template1.date_deadline),
            ('tag_ids', 'in', template1.tag_ids.mapped('id')),
        ])
        self.assertTrue(task1, "Failed creating 1 task by template.")
        template2 = self.browse_ref(
            'project_task_template.project_task_template_2')
        task2 = ProjectTask.search([
            ('project_id', '=', project.id),
            ('user_id', '=', template2.user_id.id),
            ('partner_id', '=', template2.partner_id.id),
            ('date_deadline', '=', template2.date_deadline),
            ('tag_ids', 'in', template2.tag_ids.mapped('id')),
        ])
        self.assertTrue(task2, "Failed creating 2 task by template.")

