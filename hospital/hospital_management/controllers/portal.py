from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class AppointmentPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        print("HOSPITAL_MANAGEMENT", counters)
        values = super()._prepare_home_portal_values(counters)
        if 'appointment_count' in counters:
            values['appointment_count'] = request.env['hospital.appointment'].sudo().search_count([
                ('patient_id', '=', request.env.user.partner_id.id)
            ])
        return values
        # if 'project_count' in counters:
        #     values['project_count'] = request.env['project.project'].search_count([]) \
        #         if request.env['project.project'].check_access_rights('read', raise_exception=False) else 0
        # if 'task_count' in counters:
        #     values['task_count'] = request.env['project.task'].search_count([('project_id', '!=', False)]) \
        #         if request.env['project.task'].check_access_rights('read', raise_exception=False) else 0
        # return values

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
