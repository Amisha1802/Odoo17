from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta

import base64
import itertools
from xlrd import open_workbook

import logging

logger = logging.getLogger(__name__)


class ImportEmployees(models.TransientModel):
    _name = 'import.employees'
    _description = 'Import Employees'

    file = fields.Binary('File', required=True, attachment=True)
    import_warning = fields.Text('Import Summary', readonly='1')
    name_format = fields.Selection([
        ('first_last', 'First Name, Last Name'),    
        ('last_first', 'Last Name, First Name')
    ], string='Name Format', required=True, default='first_last')
    partner_update = fields.Boolean('Update Partner?', default=False)
    user_create = fields.Boolean('Create User?', default=False)


    def get_date(self, date):
        
        if isinstance(date, str):
            # Process date as a string
            date = date.strip()
            try:
                k = datetime.strptime(date, "%d/%m/%y").date()
                return k
            except ValueError:
                print("Invalid date format in string:", date)
                return None

        elif isinstance(date, (float, int)):
            # Process date as an Excel serial date
            excel_start_date = datetime(1899, 12, 30)  # Excel serial date starts from this day
            try:
                k = (excel_start_date + timedelta(days=date)).date()
                return k
            except Exception as e:
                print("Error processing Excel serial date:", e)
                return None

        else:
            print("Unsupported date format:", date)
            return None


    def get_integer(self, value):
        if isinstance(value, (int, float)):
            # Convert numeric values to integer
            return int(value)
        elif isinstance(value, str):
            # Strip whitespace and convert string to integer
            return int(value.strip())
        else:
            # Return None for unsupported types
            return None

    def get_name(self, names, order):
        name_parts = [part.strip() for part in names.split(',')]
        
        if len(name_parts) != 2:
            return "Invalid name format. Use 'FirstName, LastName'"
        
        first_name, last_name = name_parts
        
        if order == 'first_last':
            return f"{first_name} {last_name}"
        elif order == 'last_first':
            return f"{first_name} {last_name}"
        else:
            return "Invalid order selection"


    def do_import_employees(self):
        employee_pool = self.env['hr.employee']
        partner_pool = self.env['res.partner']
        user_pool = self.env['res.users']

        book = open_workbook(file_contents=base64.b64decode(self.file))
        sheet = book.sheet_by_index(0)

        # Create an import log
        log = self.env['import.log'].create({
            'name': 'Employee Import: %s' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'success',
            'summary': 'Processing...',
        })

        skip_rows = 1
        col_map = {}
        count = 0
        create_count = 0
        update_count = 0
        skipped_count = 0

        for row in map(sheet.row, range(sheet.nrows)):
            if count == 0:
                col_index = 0
                for col in row:
                    col_map[col.value.replace(" ", "").lower()] = col_index
                    col_index += 1
                if 'employeeid' not in col_map:
                    raise UserError('No employee ID column found. Please upload a valid file.')
            count += 1
            if count <= skip_rows:
                continue

            employee_number = row[col_map['employeeid']].value
            if not employee_number:
                continue

            name = self.get_name(row[col_map['employeename']].value.strip(), self.name_format)
            job_position = row[col_map['jobposition']].value.strip()
            private_street = row[col_map['privateaddressline1']].value.strip()
            private_street2 = row[col_map['privateaddressline2']].value.strip()
            private_email = row[col_map['email']].value.strip()
            private_phone = str(row[col_map['homephone']].value).strip()
            gender = row[col_map['gender']].value.strip()
            birthday = self.get_date(row[col_map['dateofbirth']].value)
            original_hire_date = self.get_date(row[col_map['originalhiredate']].value)
            identification_id = str(row[col_map['sin']].value).strip()
            emergency_contact = row[col_map['emergencycontact(firstname)']].value.strip()
            emergency_phone = row[col_map['emergencycontactphone']].value.strip()
            registration_number = self.get_integer(row[col_map['employeeid']].value)

            job_id = self.env['hr.job'].search([('name', '=', job_position)], limit=1)
            if not job_id:
                job_id = self.env['hr.job'].create({'name': job_position})

            employee_data = {
                'name': name,
                'job_id': job_id.id,
                'private_street': private_street,
                'private_street2': private_street2,
                'private_email': private_email,
                'private_phone': private_phone,
                'gender': 'male' if gender.lower() == 'male' else 'female',
                'birthday': birthday,
                'original_hire_date': original_hire_date,
                'identification_id': identification_id,
                'emergency_contact': emergency_contact,
                'emergency_phone': emergency_phone,
                'registration_number': registration_number,
            }

            # Process employee creation or update
            try:
                employee = employee_pool.search([('registration_number', '=', registration_number)], limit=1)
                if employee:
                    employee.write(employee_data)
                    update_count += 1
                else:
                    employee = employee_pool.create(employee_data)
                    create_count += 1
            except Exception as e:
                skipped_count += 1
                log.status = 'failed'

        # Generate import summary
        summary = (
            "Import completed.\n"
            "Total Lines in File: %s\n"
            "Employees Created: %s\n"
            "Employees Updated: %s\n"
            "Lines Skipped: %s" % (count - 1, create_count, update_count, skipped_count)
        )
        print(summary)

        # Update the log with summary and attach the imported file
        log.write({
            'summary': summary,
            'file': self.file,
        })

        # Create the import employees record and link it to the log
        import_id = self.env['import.employees'].create({
            'import_warning': summary,  # Pass summary to import.employees
            'file': self.file,  # Attach the imported file
        })

        return {
            'name': 'Import Employees',
            'view_mode': 'form',
            'res_id': import_id.id,
            'res_model': 'import.employees',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
