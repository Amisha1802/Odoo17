from odoo import models, fields, api, _
import pytz
from datetime import date

class HospitalAppointment(models.Model):
    _name = 'hospital.appointment'
    _description = 'Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "appointment_date desc"

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        result = super(HospitalAppointment, self).fields_view_get(view_id,
                                                              view_type,
                                                              toolbar=toolbar,
                                                              submenu=submenu)

    def delete_lines(self):
        for rec in self:
            user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
            time_in_timezone = pytz.utc.localize(rec.appointment_datetime).astimezone(user_tz)
            print("Time in UTC -->", rec.appointment_datetime)
            print("Time in Users Timezone -->", time_in_timezone)
            rec.appointment_lines = [(5, 0, 0)]

    def print_report(self):
        return self.env.ref('hospital_management.action_appointment_report_hospital').report_action(self)

    def action_confirm(self):
        for rec in self:
            patient = self.env['res.partner'].search([('id', '=', 19)])
            print("patient_name...", patient.patient_name)
            print("sequence...", patient.name_seq)
            print("Display Name...", patient.display_name)

            product_category = self.env['product.category'].search([]).mapped('name')
            product_category_context = self.env['product.category'].with_context(lang='ar_SY').search([]).mapped('name')
            print("product_category...", product_category)
            print("product_category_context...", product_category_context)
            
            rec.state = 'confirm'


    def action_done(self):
        for rec in self:
            rec.state = 'done'
  
    @api.model
    def create(self, vals):
        # overriding the create method to add the sequence
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hospital.appointment') or _('New')
        result = super(HospitalAppointment, self).create(vals)
        return result

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for rec in self:
            return {'domain': {'order_id': [('partner_id', '=', rec.partner_id.id)]}}

    @api.model
    def default_get(self, fields):
        res = super(HospitalAppointment, self).default_get(fields)
        print("test......")
        res['patient_id'] = 1
        res['notes'] = 'Take Care!'
        return res

    name = fields.Char(string='Appointment ID', required=True, copy=False, readonly=True,
                       index=True, default=lambda self: _('New'))
    date = fields.Date(string="Date", default= lambda self: date.today(), readonly=True)
    patient_id = fields.Many2one('res.partner', string='Patient', required=True)
    email = fields.Char(string="Email", help="Patient's Email.")
    doctor_id = fields.Many2one('hospital.doctor', string='Doctor')
    patient_age = fields.Integer('Age', related='patient_id.patient_age')
    notes = fields.Text(string="Registration Note")
    doctor_note = fields.Text(string="Note", track_visibility='onchange')
    appointment_lines = fields.One2many('hospital.appointment.lines', 'appointment_id', string='Appointment Lines')
    pharmacy_note = fields.Text(string="Note", track_visibility='always')
    appointment_date = fields.Date(string='Appointment Date')
    appointment_datetime = fields.Datetime(string='Date Time')
    partner_id = fields.Many2one('res.partner', string="Customer")
    order_id = fields.Many2one('sale.order', string="Visit Order")
    amount = fields.Float(string="Total Amount")
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirm'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, default='draft')


class HospitalAppointmentLines(models.Model):
    _name = 'hospital.appointment.lines'
    _description = 'Appointment Lines'

    product_id = fields.Many2one('product.product', string='Medicine')
    product_qty = fields.Integer(string="Quantity")
    appointment_id = fields.Many2one('hospital.appointment', string='Appointment ID')
    morn = fields.Boolean(string="Morning")
    noon = fields.Boolean(string="Afternoon")
    eve = fields.Boolean(string="Night")
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")