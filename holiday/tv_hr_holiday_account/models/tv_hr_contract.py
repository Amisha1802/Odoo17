from odoo import models, fields, api, _

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'
    
    is_generate_accounting_entry = fields.Boolean(
        string='Generate Accounting Entry',
        default=False,
        help="To generate Accounting Entry for Leave"
    )
    leave_expense_account_id = fields.Many2one(
        'account.account',
        string='Leave Expense Account',
        required=True,
        help="Expense account for Leaves of Employees"
    )
    leave_provision_account_id = fields.Many2one(
        'account.account',
        string='Provision Account',
        required=True,
        help="Provision for Allocation of Leaves"
    )

class HrContract(models.Model):
    _name = 'hr.contract'
    _inherit = ['hr.contract', 'analytic.mixin']