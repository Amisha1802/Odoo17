from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleInherit(WebsiteSale):
    @http.route([
        "'/shop'",
        "'/shop/page/<int:page>'",
        '''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>''',
        '''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True, sitemap=True)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        # Call the parent `shop` method and log results
        res = super(WebsiteSaleInherit, self).shop(page=page, category=category, search=search, ppg=ppg, **post)
        request._logger.info("Website Hospital Management accessed shop with response: %s", res)
        return res

class Hospital(http.Controller):

    @http.route('/hospital/patient/', type='http', website=True, auth='user')
    def hospital_patient(self, **kw):
        """Renders a page to display patients."""
        patients = request.env['res.partner'].sudo().search([])
        return request.render("hospital_management.patients_page", {
            'patients': patients
        })

    @http.route('/update_patient', type='json', auth='user')
    def update_patient(self, **rec):
        """Updates a patient record."""
        if request.jsonrequest:
            patient_id = rec.get('id')
            if patient_id:
                patient = request.env['res.partner'].sudo().search([('id', '=', patient_id)])
                if patient:
                    patient.sudo().write(rec)
                    return {'success': True, 'message': 'Patient Updated'}
        return {'success': False, 'message': 'Invalid Request'}

    @http.route('/create_patient', type='json', auth='user')
    def create_patient(self, **rec):
        """Creates a new patient."""
        if request.jsonrequest:
            name = rec.get('name')
            email = rec.get('email')
            if name:
                vals = {
                    'patient_name': name,
                    'email': email,
                }
                new_patient = request.env['res.partner'].sudo().create(vals)
                return {'success': True, 'message': 'Patient Created', 'id': new_patient.id}
        return {'success': False, 'message': 'Invalid Request'}

    @http.route('/get_patients', type='json', auth='user')
    def get_patients(self):
        """Fetches all patient records."""
        patients_rec = request.env['res.partner'].sudo().search([])
        patients = [{
            'id': rec.id,
            'name': rec.patient_name,
            'sequence': rec.name_seq,
        } for rec in patients_rec]
        return {
            'status': 200,
            'response': patients,
            'message': 'All Patients Returned'
        }