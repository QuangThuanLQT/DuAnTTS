from odoo import models, fields, api

class MaterialPlan(models.Model):
    _inherit = 'material.plan'

    stock_picing_id = fields.Many2one('stock.picking', string="Stock Picking")

    @api.onchange('task_id')
    def _onchange_task(self):
        self.message = "Dear %s" % (self.task_id.name or "")
        import pdb; pdb.set_trace()

        # return {
        #          {'value':{
        #                     'description': 
        #                     'product_uom_qty':
        #                     'product_uom':
        #                     'product_id':
        #             }}
        #             }
