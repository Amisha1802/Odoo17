from odoo import models, fields, api,  _
from datetime import date
from odoo.exceptions import ValidationError



class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    patient_name = fields.Char(string='Patient Name')



    def _onchange_patient_id(self):
        """Fetch patient history when patient is selected."""
        if self.patient_id and self.patient_id.is_patient:
            self.show_patient_fields = [(5, 0, 0)]


class HospitalPatient(models.Model):
    _name = 'hospital.patient'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Patient Record'

    patient_age = fields.Integer('Age', compute="_compute_age")

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_patient = fields.Selection([
                                ('patient', 'Patient'),
                                ('visitor', 'Visitor'),    
                                ], default='patient')
    name = fields.Char(string="Emergency Number")
    contact_num = fields.Char(string="Contact Number", required=True, help="Patient's Contact Number.")
    name_seq = fields.Char(string='Patient ID', required=True, copy=False, readonly=True,
        index=True, default=lambda self: _('New'))
    email = fields.Char(
        string="Email", help="Patient's Email.")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], default='male', string="Gender")
    patient_name = fields.Many2one('res.partner', string='Patient Name', required=True,  track_visibility="always")
    date_of_birth = fields.Date(string="DOB", required=True)
    patient_age = fields.Integer('Age', compute="_compute_age")
    notes = fields.Text(string="Registration Note")
    appointment_count = fields.Integer(string='Appointment', compute='get_appointment_count')
    doctor_id = fields.Many2one('hospital.doctor', string="Doctor" )
    doctor_gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Doctor Gender")

    def print_report(self):
        return self.env.ref('hospital_management.action_report_patient_card').report_action(self)

    # @api.model
    # def test_cron_job(self):
    #     print("Abcd")

    @api.depends("date_of_birth")
    def _compute_age(self):
        """Compute the age from the date of birth."""
        for record in self:
            if record.date_of_birth:
                today = date.today()
                old = today.year - record.date_of_birth.year
                # Adjust for the case where the birthday hasn't occurred this year yet
                if (today.month, today.day) < (record.date_of_birth.month, record.date_of_birth.day):
                    old -= 1
                record.patient_age = old
            else:
                record.patient_age = 0  # Default age when DOB is not provided
    @api.model
    def name_get(self):
        # name get function for the model executes automatically
        res = []
        for rec in self:
            res.append((rec.id, '%s - %s' % (rec.patient_name, rec.name_seq)))
        return res

    # @api.model
    # def _name_search(self, name='', args=None, operator='ilike', limit=100):
    #     if args is None:
    #         args = []
    #     domain = args + ['|', ('name_seq', operator, name), ('patient_name', operator, name)]
    #     return super(ResPartner, self).search(domain, limit=limit).name_get()

    @api.constrains('identification_id')
    def check_identification_id(self):
        for rec in self:
            if len(rec.identification_id) != 11:
                raise ValidationError(_('Must be 11 Characters'))

    def open_patient_appointments(self):
        return {
            'name': _('Appointments'),
            'domain': [('patient_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'hospital.appointment',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_appointment_count(self):
        count = self.env['hospital.appointment'].search_count([('patient_id', '=', self.id)])
        self.appointment_count = count

    @api.onchange('doctor_id')
    def set_doctor_gender(self):
        for rec in self:
            if rec.doctor_id:
                rec.doctor_gender = rec.doctor_id.gender

    # def action_send_card(self):
    #     # sending the patient report to patient via email
    #     template_id = self.env.ref('om_hospital.patient_card_email_template').id
    #     template = self.env['mail.template'].browse(template_id)
    #     template.send_mail(self.id, force_send=True)

    @api.depends('patient_name')
    def _compute_upper_name(self):
        for rec in self:
            rec.patient_name_upper = rec.patient_name.upper() if rec.patient_name else False

    @api.depends('patient_age')
    def set_age_group(self):
        for rec in self:
            if rec.patient_age:
                if rec.patient_age < 18:
                    rec.age_group = 'minor'
                else:
                    rec.age_group = 'major'

    @api.model
    def create(self, vals):
        if vals.get('name_seq', _('New')) == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('hospital.patient.sequence') or _('New')
        result = super(HospitalPatient, self).create(vals)
        return result
