from odoo import models, fields, api

class MaterialPlanning(models.Model):
    _inherit = 'stock.picking'

    material_plan_ids = fields.One2many('material.plan','material_task_id', string="Material")
    
    @api.onchange('task_id')
    def _onchange_task(self):
        for obj in self:
            material_plan_ids = []
            for material in obj.task_id.material_plan_ids:
                material_plan_ids.append((0, 0, {
                    'description': material.description,
                    'product_uom_qty': material.product_uom_qty,
                    'product_uom': material.product_uom,
                    'product_id': material.product_id,
                }))
            # import pdb; pdb.set_trace()
            obj.update({'material_plan_ids' : material_plan_ids})