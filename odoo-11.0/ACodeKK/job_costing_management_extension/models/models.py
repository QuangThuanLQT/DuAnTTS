# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProjectProject(models.Model):
    _inherit = 'project.project'

    sub_contractor_ids = fields.Many2many(
        'res.partner', 
        string="Sub Contractor",
        domain=[('is_subcontractor', '=', True)],
        context={'default_is_subcontractor': True},
    )
    notes_count = fields.Integer(
        compute='_compute_notes_count', 
        string="Notes",
        store=False,
    )
    # 


    site_location = fields.Many2many('stock.location', 'site_loc', string="Site Location")

    job_estimate_count = fields.Integer(string="Job Estimate Count", compute='compute_estimate_count')
    location_id = fields.Many2one(comodel_name='stock.location', string="Location")
    
    @api.depends()
    def compute_estimate_count(self):
        for obj in self:
            job_estimate_count = obj.env['sale.estimate.job'].search([('project_id', '=', obj.id)])
            obj.job_estimate_count = len(job_estimate_count)  

    #@api.model
    #def create(self, vals):
        #import pdb; pdb.set_trace()

    '''@api.multi
    def write(self, vals):
        
        # ids = vals.values()[0][0][2]
        #contractors = self.env['res.partner'].browse(ids)
        return super(ProjectProject, self).create(vals)'''


class Task(models.Model):
    _inherit = "project.task"

    @api.multi
    def _get_subtask_count(self):
        for task in self:
            task.subtask_count = len(task.child_task_ids)  

class JobCosting(models.Model):
    _inherit = 'job.costing'

    @api.onchange('project_id')
    def onchange_project_id(self):
        for obj in self:
            obj.update({'partner_id': obj.project_id.partner_id.id})
        return

class Product(models.Model):
    _inherit = 'product.product'

    boq_type = fields.Selection([
        ('eqp_machine', 'Machinery / Equipment'),
        ('worker_resource', 'Worker / Resource'),
        ('work_cost_package', 'Work Cost Package'),
        ('subcontract', 'Subcontract')], 
        string='BOQ Type', 
        help="This will be used in Material Request / BOQ while calculating total cost"
        " for each category/type of material/labour.",
    )

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    project_id = fields.Many2one(
        'project.project',
        string='Project',
    )
