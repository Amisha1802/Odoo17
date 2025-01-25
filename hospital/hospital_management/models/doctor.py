from odoo import models, fields

class HospitalDoctor(models.Model):
    _name = 'hospital.doctor'
    _inherits = {'res.partner': 'related_patient_id'}
    _description = 'Doctor Record'

    # doc_name = fields.Char(string='Doctor Name', required=True)
    specialization = fields.Char(string="Specialization")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], default='male', string="Gender")
    user_id = fields.Many2one('res.users', string='Related User')
    patient_id = fields.Many2one('res.partner', string='Related Patient')
    related_patient_id = fields.Many2one('res.partner', string='Doctor Name')