{
    'name': 'Hospital Management',
    'version': '1.0',
    'summary': 'A module for managing hospital operations',
    'author': 'Techvertis',
    'category': 'Healthcare',
    'depends': ['base', 'mail', 'sale', 'board', 'website'],  # Ensure all dependencies are updated
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'wizards/create_appointment.xml',
        'views/patient_views.xml',
        'views/appointment_views.xml',
        'views/lab_views.xml',
        'views/doctor_views.xml',
        'views/portal_template_views.xml',
        'views/template_views.xml',
        'views/dashboard.xml',
        'views/menu.xml',
        'reports/appointment_report_views.xml',
        'reports/patient_card_views.xml'
    ],

    'installable': True,
    'application': True,
}