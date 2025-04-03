{
    'name': 'TV Contact Notes',
    'version': '1.0',
    'summary': 'Custom module to add notes with attachments to contacts',
    'author': 'Techvertis',
    'category': 'Contacts',
    'depends': ['base', 'contacts', 'project'],  # Ensure all dependencies are updated
    'data': [
		'security/ir.model.access.csv',
        'views/contact_notes_views.xml',        
    ],

    'installable': True,
    'application': True,
}
