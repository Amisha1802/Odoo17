from odoo import models, fields, api, _

class CreateAppointment(models.TransientModel):
    _name = 'create.appointment'
    _description = 'Create Appointment Wizard'

    patient_id = fields.Many2one(
        'res.partner', 
        string="Patient", 
        required=True
    )
    doctor_id = fields.Many2one(
        'hospital.doctor', 
        string="Doctor"
    )
    appointment_date = fields.Date(
        string="Appointment Date", 
        required=True
    )
    # patient_history = fields.Text(
    #     string="Patient History", 
    #     readonly=True
    # )

    # def action_get_data(self):
    #     """Fetch and display patient history on button click."""
    #     if not self.patient_id:
    #         raise ValueError(_("Please select a patient first."))
    #     self.patient_history = self.patient_id.get_patient_history()

    def print_report(self):
        """Generate and return a report."""
        data = {
            'model': 'create.appointment',
            'form': self.read()[0],
        }
        return self.env.ref('hospital_management.action_hospital_appointment_report').with_context(landscape=True).report_action(self, data=data)

    def delete_patient(self):
        """Delete the selected patient."""
        for rec in self:
            if rec.patient_id:
                rec.patient_id.unlink()
            else:
                raise ValueError(_("No patient selected to delete."))

    def create_appointment(self):
        """Create a new appointment and redirect to its form view."""
        if not self.patient_id or not self.appointment_date:
            raise ValueError(_("Please provide both patient and appointment date."))
        
        vals = {
            'patient_id': self.patient_id.id,
            'appointment_date': self.appointment_date,
            'notes': _('Created From The Wizard/Code'),
        }
        
        # Log a message on the patient's chatter
        self.patient_id.message_post(
            body=_("An appointment has been created."),
            subject=_("Appointment Creation")
        )
        
        # Create the appointment record
        new_appointment = self.env['hospital.appointment'].create(vals)

        # Prepare context for redirecting to the form view of the created appointment
        context = dict(self.env.context or {})
        context['form_view_initial_mode'] = 'edit'

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'hospital.appointment',
            'res_id': new_appointment.id,
            'context': context,
        }
