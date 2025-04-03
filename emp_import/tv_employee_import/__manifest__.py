# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'TV HR Employee Import',
    'version': '1.0',
    'summary': 'Importing the hr_employee csv',
    'description': """
    """,
    'author': 'Techvertis',
    'category': 'Human Resource',
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee.xml',
        'views/hr_emp_log.xml',
        'wizard/hr_employee_import.xml',
    ],
    
    'installable': True,
    'application': True,
}
