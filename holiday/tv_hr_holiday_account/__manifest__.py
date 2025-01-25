{
    'name': 'TV HR Holidays Account',
    'version': '1.0',
    'summary': 'Generate accounting entries for leave allocations and usage',
    'author': 'Invoertis Solutions',
    'category': 'Human Resources',
    'depends': ['base', 'hr_holidays', 'account', 'analytic'],  # Ensure all dependencies are updated
    'data': [
		'views/tv_hr_holidays_views.xml',        
        'views/tv_hr_leave_views.xml',        
        'views/tv_hr_allocation_views.xml', 
        'views/hr_contract_views.xml',       
    ],

    'installable': True,
    'application': True,
}