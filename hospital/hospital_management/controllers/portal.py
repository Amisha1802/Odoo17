from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class AppointmentPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        print("HOSPITAL_MANAGEMENT", counters)
        values = super()._prepare_home_portal_values(counters)
        print("=2222222==", request.env['hospital.appointment'].check_access_rights('read', raise_exception=False))
        if 'appointment_count' in counters:
            values['appointment_count'] = request.env['hospital.appointment'].search_count([
                ('patient_id', '=', request.env.user.partner_id.id)
            ])
        return values

    @http.route(['/my/appointments'], type='http', auth="user", website=True)
    def portal_my_appointments(self, **kwargs):
        print("PORTAL", self, kwargs)
        appointments = request.env['hospital.appointment'].sudo().search([
            ('patient_id', '=', request.env.user.patient_id.id)
        ])
        return request.render('hospital_management.portal_appointment_template', {
            'appointments': appointments,
        })

    @http.route(['/my/appointments/<int:appointment_id>'], type='http', auth="user", website=True)
    def portal_appointment_detail(self, ticket_id, **kwargs):
        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)
        if not appointment.exists():
            return request.not_found()
        return request.render('hospital_management.portal_my_appointments', {
            'appointment': appointment,
        })

    def _prepare_portal_layout_values(self):
        """Prepares layout values for the portal."""
        values = super(AppointmentPortal, self)._prepare_portal_layout_values()
        values['appointment_count'] = request.env['hospital.appointment'].sudo().search_count([])
        return values

    @http.route(['/my/appointments'], type='http', auth='user', website=True)
    def portal_my_appointments(self, **kw):
        """Displays appointments in the portal."""
        values = self._prepare_portal_layout_values()
        # Only fetch appointments related to the logged-in user
        appointments = request.env['hospital.appointment'].sudo().search([
            ('patient_id', '=', request.env.user.patient_id.id)
        ])
        values.update({'appointments': appointments})
        return request.render("hospital_management.portal_my_appointments", values)
