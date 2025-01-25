from odoo import api, models, _


class AppointmentReport(models.AbstractModel):
    _name = 'report.hospital_management.appointment_report'
    _description = 'Appointment Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if data['form']['patient_id']:
            appointments = self.env['hospital.appointment'].search([('patient_id', '=', data['form']['patient_id'][0])])
        else:
            appointments = self.env['hospital.appointment'].search([])
        print("data", data)
        return {
            'doc_model': 'hospital.patient',
            'appointments': appointments,
            'data': data['form']
        }
