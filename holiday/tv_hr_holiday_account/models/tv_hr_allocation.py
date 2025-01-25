from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    move_id = fields.Many2one(
        'account.move',
        string="Journal Entry",
        readonly=True,
        help="Journal entry linked to this leave allocation."
    )
    employee_warning_message = fields.Char(
        string="Warning Message", 
        readonly=True,
        help="The Non Contracted Employee Warning."
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

    def action_refuse(self):
        """Cancel journal entry when allocation is refused."""
        res = super(HrLeaveAllocation, self).action_refuse()
        for allocation in self:
            if allocation.move_id:
                allocation.move_id.button_cancel()
        return res

    def action_draft(self):
        """Set journal entry to draft when allocation is reset to draft."""
        res = super(HrLeaveAllocation, self).action_draft()
        for allocation in self:
            if allocation.move_id and allocation.move_id.state == 'posted':
                allocation.move_id.button_draft()
        return res

    def action_validate(self):
        print("////////////////////////",self)
        res = super(HrLeaveAllocation, self).action_validate()
        self.action_employee_warning_message()
        print("RES----ALLOCATION-----Super",res, self)
        for allocation in self:
            print (">>>>>>>>>>>>>>>>>>>>>>>>>>>",self, allocation, allocation.employee_id, allocation.employee_ids.ids)
            contract = self.env['hr.contract'].sudo().search([
                ('employee_id', '=', allocation.employee_id.id),
                ('state', '=', 'open')
            ], limit=1)
            # Check if accounting entry needs to be generated
            if contract and contract.state == 'open': 
                if allocation.holiday_status_id.is_generate_accounting_entry and allocation.state == 'validate':
                    print(contract, contract.state, allocation.holiday_status_id.is_generate_accounting_entry, allocation.state)                
                    leave_type = allocation.holiday_status_id

                    # Compute leave allocation amount
                    wages = contract.wage
                    print("EMPLOYEE++++++WAGES",wages)
                    per_day_wage = wages / 30
                    print("EMPLOYEE++++++PER%DAYWAGE",per_day_wage)
                    amount = per_day_wage * allocation.number_of_days
                    print(amount)

                    if not leave_type.leave_expense_account_id or not leave_type.leave_provision_account_id:
                        raise UserError(_("Please configure Leave Expense and Provision accounts for the leave type."))

                    # Generate accounting entry
                    if allocation.allocation_type == 'regular':
                        allocation.sudo()._create_allocation_accounting_entry(
                            amount,
                            leave_type,
                            allocation.employee_id.work_contact_id,
                            f"Leave Allocation - {allocation.employee_id.name} ({allocation.number_of_days} days)"
                        )
                    else: 
                        allocation.sudo()._create_accrual_journal_entry(
                            amount,
                            leave_type,
                            allocation.employee_id.work_contact_id,
                            f"Accural Allocation - {allocation.employee_id.name} ({allocation.number_of_days} days)"
                        )
        return res


    def _create_allocation_accounting_entry(self, amount, leave_type, partner_id, description):
        print("TV----ALLOCATION---HOLIDAY")
        journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
        if not journal:
            raise UserError(_("No general journal found for accounting entry creation."))

        # Prepare move values
        move_vals = {
            'journal_id': journal.id,
            'ref': description,
            'line_ids': [
                (0, 0, {
                    'account_id': leave_type.leave_provision_account_id.id,  # Provision account
                    'debit': amount,
                    'credit': 0,
                    'partner_id': partner_id.id,
                    'name': _("Allocation Provision for %s") % self.employee_ids.name,
                    'analytic_distribution': self.employee_ids.contract_id.analytic_distribution,
                }),
                (0, 0, {
                    'account_id': leave_type.leave_expense_account_id.id,  # Expense account
                    'debit': 0,
                    'credit': amount,
                    'partner_id': partner_id.id,
                    'name': _("Leave Expense Allocation for %s") % self.employee_ids.name,
                    'analytic_distribution': self.employee_ids.contract_id.analytic_distribution,
                }),
            ],
        }
        # Create and post the accounting entry
        move = self.env['account.move'].create(move_vals)
        print("????----ALLOCATION--", move)
        move.action_post()
        self.move_id = move.id
        return move



    def _process_accrual_plans(self):
        """Override _process_accrual_plans to create journal entries for accrual allocations. """
        print("-------UPDATING ACCRUALS-----------", self)
        # Call the original method to perform base functionality
        res = super(HrLeaveAllocation, self)._process_accrual_plans()

        for accrual in self:
            print("______CREATING ACCRUAL ENTRY_____")

            # Check if the allocation is of type 'accrual' and in the validated state
            if accrual.allocation_type == 'accrual' and accrual.state == 'validate':
                # Get the employee's contract
                contract = accrual.employee_id.contract_id
                if not contract or contract.state != 'open':
                    print("No valid contract found for employee:", accrual.employee_id.name)
                    continue

                print("Contract found for employee:", contract)
                leave_type = accrual.holiday_status_id
                print("Leave Type:", leave_type)

                # Compute accrual amount
                wages = contract.wage  # Default to 0.0 if wages are not set
                print("EMPLOYEE ACCURAL WAGES",wages)
                per_day_wage = wages / 30
                print("EMPLOYEE ACCURAL PER%DAYWAGE",per_day_wage)
                accrual_days = accrual.number_of_days
                amount = per_day_wage * accrual_days
                print(f"Computed Amount: {amount} for {accrual_days} days")

                if amount > 0:  # Only create a journal entry if the amount is positive
                    # Create journal entry for the accrual
                    accrual.sudo()._create_accrual_journal_entry(
                        amount=amount,
                        leave_type=leave_type,
                        partner_id=accrual.employee_id.work_contact_id,
                        description=f"Accrual Update - {accrual.employee_id.name} ({accrual_days} days)"
                    )
        return res

    def _get_future_leaves_on(self, date):
        """Override _get_future_leaves_on to add journal entry creation for future leave accruals."""
        # Call the original method to get future leave balances
        print("FUTURE ACCURAL UPDATE",self)
        future_leaves = super(HrLeaveAllocation, self)._get_future_leaves_on(date)

        for accrual in self.filtered(lambda l: l.allocation_type == 'accrual' and l.state == 'validate'):
            # Ensure the employee has an active contract
            contract = self.env['hr.contract'].sudo().search([
                ('employee_id', '=', accrual.employee_id.id),
                ('state', '=', 'open')
            ], limit=1)

            if not contract:
                print(f"No active contract for employee {accrual.employee_id.name}, skipping journal entry.")
                continue
            
            print("Contract found for employee:", contract)

            # Compute future accrual amount
            wages = contract.wage 
            print("EMPLOYEE FUTURE ACCURAL WAGES",wages)
            per_day_wage = wages / 30  # Assuming 30 days in a month
            print("EMPLOYEE FUTURE ACCURAL PER%DAYWAGE",per_day_wage)
            accrual_days = accrual.number_of_days_display  # Use the display number of days
            amount = per_day_wage * accrual_days
            print(amount)

            if amount > 0:
                # Check if required accounts are configured
                leave_type = accrual.holiday_status_id
                if not leave_type.leave_expense_account_id or not leave_type.leave_provision_account_id:
                    raise UserError(_(
                        f"Please configure Leave Expense and Provision accounts for the leave type '{leave_type.name}'."
                    ))

                # Create journal entry for the future accrual
                self.sudo()._create_future_leave_journal_entry(
                    amount=amount,
                    leave_type=leave_type,
                    partner_id=accrual.employee_id.work_contact_id,
                    description=f"Accrual Update - {accrual.employee_id.name} ({accrual_days} days)"
                )
        return future_leaves


    def _create_future_leave_journal_entry(self, amount, leave_type, partner_id, description):
        """Create a journal entry for future leave accruals."""
        print(f"Creating future accrual journal entry for {self.employee_id.name}")
        journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
        if not journal:
            raise UserError(_("No general journal found for accounting entry creation."))

        # Prepare journal entry values
        move_vals = {
            'journal_id': journal.id,
            'ref': description,
            'line_ids': [
                # Debit: Expense Account
                (0, 0, {
                    'account_id': leave_type.leave_expense_account_id.id,
                    'debit': amount,
                    'credit': 0,
                    'partner_id': partner_id.id,
                    'name': _("Accrual Expense for Future Leave"),
                }),
                # Credit: Provision Account
                (0, 0, {
                    'account_id': leave_type.leave_provision_account_id.id,
                    'debit': 0,
                    'credit': amount,
                    'partner_id': partner_id.id,
                    'name': _("Provision for Future Leave Accrual"),
                }),
            ],
        }

        # Create and post the journal entry
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        print(f"Journal Entry Created: {move.id}")
        self.move_id = move.id
        return move



    def _create_accrual_journal_entry(self, amount, leave_type, partner_id, description):
        """Create a journal entry for the accrual update."""
        print("TV----ACCURAL-----ALLOCATION---HOLIDAY", amount, leave_type, partner_id, description)
        journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
        if not journal:
            raise UserError(_("No general journal found for accounting entry creation."))

        # Prepare journal entry values
        move_vals = {
            'journal_id': journal.id,
            'ref': description,
            'line_ids': [
                # Debit: Expense Account
                (0, 0, {
                    'account_id': leave_type.leave_expense_account_id.id,  # Expense account
                    'debit': amount,
                    'credit': 0,
                    'partner_id': partner_id.id,
                    'name': _("Accrual Provision for %s") % self.employee_ids.name,
                    'analytic_distribution': self.employee_ids.contract_id.analytic_distribution,
                }),
                # Credit: Provision Account
                (0, 0, {
                    'account_id': leave_type.leave_provision_account_id.id,  # Provision account
                    'debit': 0,
                    'credit': amount,
                    'partner_id': partner_id.id,
                    'name':_("Accrual Expense for %s") % self.employee_ids.name,
                    'analytic_distribution': self.employee_ids.contract_id.analytic_distribution,
                }),
            ],
        }

        # Create and post the journal entry
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        self.move_id = move.id
        return move 