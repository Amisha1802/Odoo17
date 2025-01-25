from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    move_id = fields.Many2one(
        'account.move',
        string="Journal Entry",
        readonly=True,
        help="Journal entry linked to this leave request."
    )
    employee_warning_message = fields.Char(
        string="Warning Message", 
        readonly=True,
        help="The Non_contracted Employee Warning."
    )

    def action_employee_warning_message(self):
        """Generate a warning message for employees with inactive or missing contracts."""
        print("_compute_employee_warning_message", self)
        for record in self:
            invalid_employees = []
            for employee in record.employee_ids:
                # Use sudo() to ensure contract access bypassing security rules
                contract = self.env['hr.contract'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'open')
                ], limit=1)
                
                # Add to invalid employees if no valid contract is found
                if not contract:
                    invalid_employees.append(employee.name)

            # Set the warning message only if there are invalid employees
            if invalid_employees:
                employee_names = ", ".join(invalid_employees)
                record.employee_warning_message = (
                    f"The employee contract for {employee_names} is not in the 'Running' state. "
                    "\nOnly employees with active contracts can be allocated leave."
                )
                print(f"WARNING: {record.employee_warning_message}")
            else:
                # Clear the warning message if all contracts are valid
                record.employee_warning_message = ""


    def action_view_journal_entry(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entry',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'target': 'current',
        }

    def _create_leave_accounting_entry(self, amount, leave_type, partner_id, description):
        """Create journal entry for leave allocation."""
        print("////----TV----LEAVE---HOLIDAY----////")
        journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
        if not journal:
            raise UserError(_("No general journal found for accounting entry creation."))

        # Prepare move values
        move_vals = {
            'journal_id': journal.id,
            'ref': description,
            'line_ids': [
                (0, 0, {
                    'account_id': leave_type.leave_expense_account_id.id,
                    'debit': amount,
                    'credit': 0,
                    'partner_id': partner_id.id,
                    'name': _("Provision for Leave from %s" % leave_type.leave_provision_account_id), 
                    'analytic_distribution': self.employee_ids.contract_id.analytic_distribution,
                }),
                (0, 0, {
                    'account_id': leave_type.leave_provision_account_id.id,
                    'debit': 0,
                    'credit': amount,
                    'partner_id': partner_id.id,
                    'name': _("Leave Expense from %s" % leave_type.leave_expense_account_id),
                    'analytic_distribution': self.employee_ids.contract_id.analytic_distribution,
                }),
            ],
        }

        move = self.env['account.move'].create(move_vals)
        print("//////----LEAVE----//////", move)
        move.action_post()
        self.move_id = move.id
        return move

    def action_validate(self):
        """Validate the leave request and handle journal entry creation."""
        res = super(HrLeave, self).action_validate()
        print("RES----LEAVE------Super", res, self)
        self.action_employee_warning_message()

        for leave in self:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!",self)
            employees = leave.employee_ids if leave.employee_ids else [leave.employee_id]
            for employee in employees:
                print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
                # Explicitly fetch the contract to bypass access restrictions
                contract = self.env['hr.contract'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'open')
                ], limit=1) 
                print("CONTRACT???????????", contract)

                if contract and leave.holiday_status_id.is_generate_accounting_entry and leave.state == 'validate':
                    leave_type = leave.holiday_status_id
                    wages = contract.wage  # Default to 0.0 if wages are not set
                    print("------EMPLOYEE WAGES-------=", wages)
                    per_day_wage = wages / 30
                    print("------EMPLOYEE PER DAY WAGE------=", per_day_wage)
                    amount = per_day_wage * leave.number_of_days
                    print(amount)

                    if not leave_type.leave_expense_account_id or not leave_type.leave_provision_account_id:
                        raise UserError(_("Please configure Leave Expense and Provision accounts for the leave type."))

                    leave.sudo()._create_leave_accounting_entry(
                        amount,
                        leave_type,
                        employee.work_contact_id,
                        f"Leave Allocation - {employee.name} ({leave.number_of_days} days)"
                    )
        return res


    def action_leave_request_validate(self):
        """Override leave request validation to generate accounting entries for multiple employees."""
        res = super(HrLeave, self).action_leave_request_validate()
        for leave in self:
            if leave.holiday_status_id.is_generate_accounting_entry and leave.state == 'validate':
                # Get accounts
                leave_type = leave.holiday_status_id
                debit_account = leave_type.leave_provision_account_id
                credit_account = leave_type.leave_expense_account_id

                if not leave.employee_id.contract_id:
                    raise UserError('The employee does not have an active contract.')

                wages = leave.employee_id.contract_id.wage
                per_day_wage = wages / 30
                amount = per_day_wage * leave.number_of_days

                # Generate accounting entry
                leave.sudo()._create_accounting_entry(
                    debit_account, credit_account, amount,
                    f"Leave Used - {leave.employee_id.name} ({leave.number_of_days} days)"
                )
        return res

    def action_refuse(self):
        """Cancel journal entry when allocation is refused."""
        res = super(HrLeave, self).action_refuse()
        for leave in self:
            if leave.move_id:
                if leave.move_id.state == 'posted':
                    leave.move_id.button_cancel()
                    reversal_move = leave.move_id._reverse_moves(default_values_list=[{
                        'journal_id': leave.move_id.journal_id.id,
                        'date': fields.Date.today(),
                    }], cancel=True)
                    # leave.move_id = False  # Clear the journal entry link
        return res