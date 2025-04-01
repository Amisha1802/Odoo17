import json
import logging
import base64
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

class ImportJournalEntries(models.TransientModel):
    _name = 'import.journal.entries'
    _description = 'Import Journal Entries'

    json_file = fields.Binary('JSON File', required=True, help="Upload your journal entries JSON file")
    file_name = fields.Char('Filename')

    def action_import_journals(self):
        self.ensure_one()
        try:
            file_content = base64.b64decode(self.json_file).decode('utf-8')
            data = json.loads(file_content)
            print("TRY BLOCK 4 JSON DECODE:", file_content, data)
        except Exception as e:
            print("EXCEPTION BLOCK 4 JSON DECODE")
            _logger.error("Import error: %s", str(e))
            raise ValidationError(_("Invalid JSON file format. Please check the file and try again."))

        if not data.get('GeneralJournals'):
            raise UserError(_("No journal entries found in the uploaded file."))

        processed_entries = 0
        company = self.env.company
        print("COMPANY NAME::::::::", company)

        for journal_data in data['GeneralJournals']:
            try:
                move = self._process_journal_entry(journal_data, company)
                if move:
                    processed_entries += 1
                print("TRY BLOCK 4 JOURNAL:", move)
            except Exception as e:
                print("EXCEPTION BLOCK 4 JOURNAL:")
                _logger.error("Failed to process entry %s: %s", 
                            journal_data.get('JournalBatchNumber'), str(e))
                continue

        return self._show_import_result(processed_entries)

    def _process_journal_entry(self, journal_data, company):
        """ Process a single journal entry with its lines """
        journal = self._get_or_create_journal(company)
        print("Journal 4 Preparing Entry::::::", journal)
        move = self.env['account.move'].create({
            'journal_id': journal.id,
            'ref': journal_data.get('Description', 'Imported Journal'),
            'date': self._parse_date(journal_data.get('PaymentDate')),
            'move_type': 'entry',
            'company_id': company.id,
        })
        print("Prepared Entries>>>>>", move)

        lines = []
        for line in journal_data.get('Lines', []):
            line_vals = self._prepare_move_line(line, move, company)
            lines.append((0, 0, line_vals))
            print("Prepared move lines?????????", line_vals)

        if not lines:
            raise UserError(_("No valid lines found in journal entry %s") % 
                          journal_data.get('JournalBatchNumber'))

        move.write({'line_ids': lines})
        move.action_post()
        return move

    def _prepare_move_line(self, line, move, company):
        """ Prepare values for account.move.line """
        return {
            'account_id': self._get_or_create_account(line, company).id,
            # 'partner_id': self._get_or_create_partner('VendorName', line).id,
            'name': line.get('Description', 'Imported Line'),
            'debit': abs(line.get('Debit', 0.0)),
            'credit': abs(line.get('Credit', 0.0)),
            'date': self._parse_date(line.get('Date')) or move.date,
            'currency_id': self._get_currency(line, company),
        }

    def _parse_date(self, date_str):
        """ Parse Dynamics 365 date format with timezone handling """
        try:
            if date_str.endswith('Z'):
                return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ').date()
            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S').date()
        except (ValueError, TypeError):
            return fields.Date.context_today(self)

    def _get_or_create_journal(self, company):
        """ Get or create general journal """
        journal = self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', company.id)
        ], limit=1)
        print("CHOOSING JOURNAL///////", journal)

        if not journal:
            journal = self.env['account.journal'].create({
                'name': 'General Journal',
                'code': 'GEN',
                'type': 'general',
                'company_id': company.id
            })
        return journal

    def _get_or_create_account(self, line, company):
        """ Get or create account with proper type detection """
        account_code = (line.get('Account') or '').split('|')[0].strip()
        print("ACCOUNT CODE++++++++++++++++++", account_code)
        if not account_code:
            raise ValidationError(_("Missing account code in line: %s") % line)

        account = self.env['account.account'].search([
            ('code', '=', account_code),
            ('company_id', '=', company.id)
        ], limit=1)

        if not account:
            account_type = self._determine_account_type(account_code)
            account = self.env['account.account'].create({
                'code': account_code,
                'name': line.get('AccountName', f'Imported Account {account_code}'),
                'account_type': account_type,
                'company_id': company.id,
            })
        return account

    def _determine_account_type(self, account_code):
        """ Map account codes to Odoo 17 account types """
        code_prefix = account_code[:4]
        type_mapping = {
            # Asset accounts
            '1101': 'asset_cash',          # Bank accounts
            '1102': 'asset_current',       # Petty cash
            # Liability accounts
            '2102': 'liability_payable',   # Accounts Payable
            '2103': 'liability_current',   # Accrued expenses
            # Equity accounts
            '3101': 'equity',              # Equity
            # Income/Expense
            '4101': 'income',              # Revenue
            '5101': 'expense',             # Expenses
        }
        return type_mapping.get(code_prefix, 'expense')

    # def _get_or_create_partner(self, line):
    #     """ Get or create partner with proper type detection """
    #     partner_name = line.get('VendorName') or line.get('CustomerName')
    #     if not partner_name:
    #         return False

    #     partner = self.env['res.partner'].search([('name', '=', partner_name)], limit=1)
    #     pritn("PARTNER __________", partner)
    #     if not partner:
    #         partner = self.env['res.partner'].create({
    #             'name': partner_name,
    #             'company_type': 'company',
    #             'supplier_rank': 1 if line.get('VendorName') else 0,
    #             'customer_rank': 1 if line.get('CustomerName') else 0
    #         })
    #     return partner.id

    def _get_currency(self, line, company):
        """ Handle multi-currency transactions """
        currency_code = line.get('Currency')
        if currency_code and currency_code != company.currency_id.name:
            currency = self.env['res.currency'].search(
                [('name', '=', currency_code)], 
                limit=1
            )
            return currency.id if currency else company.currency_id.id
        return company.currency_id.id

    def _show_import_result(self, count):
        """ Show final import result notification """
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Import Complete'),
                'message': _('Successfully processed %d journal entries') % count,
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window_close',
                    'infos': {'import_count': count}
                }
            }
        }