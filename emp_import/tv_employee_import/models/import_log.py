from odoo import models, fields, api
from datetime import datetime

class ImportLog(models.Model):
    _name = 'import.log'
    _description = 'Import Log'

    name = fields.Char('File Name', required=True)
    import_date = fields.Datetime('Import Date', default=fields.Datetime.now, required=True)
    status = fields.Selection([('success', 'Success'), ('failed', 'Failed')], string="Status", default='success')
    summary = fields.Text('Summary')
    file = fields.Binary(string='Imported File', readonly=True)