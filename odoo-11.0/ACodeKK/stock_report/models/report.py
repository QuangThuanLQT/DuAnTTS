
from odoo import api, models

class report_import_note(models.AbstractModel):
    _name = 'report.stock_report.report_import_note'

    @api.multi
    def render_html(self, docids, data=None):
        docargs = {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': self.env['stock.picking'].browse(docids),
            'data': data,
        }
        return self.env['report'].render('stock_report.report_import_note', docargs)