{
    'name': 'Account Import',
    'version': '1.0',
    'category': 'Custom',
    'summary': 'Neutralizes normalize_iban and modifies pretty_iban methods in res.partner.bank',
    'author': 'Techvertis',
    'depends': ['account', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_import_wizard_view.xml',
    ],
    
    'installable': True,
    'application': True,
}
