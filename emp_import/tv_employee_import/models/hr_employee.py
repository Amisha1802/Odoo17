from odoo import api, fields, models, _
from datetime import datetime

class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'

    original_hire_date = fields.Date('Original Hire Date')
    registration_number = fields.Integer('Employee ID') 