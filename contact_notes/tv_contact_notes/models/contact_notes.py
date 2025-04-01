from odoo import models, fields, api


class NotesType(models.Model):
    _name = 'notes.type'
    _description = 'Notes Type'

    name = fields.Char(string='Note Type', required=True)
    notes = fields.Html(string='Notes')
    task_id = fields.Many2one('project.task', string='Task')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    partner_id = fields.Many2one('res.partner', string='Contact')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    note_type_ids = fields.One2many('notes.type', 'partner_id', string='Note Types')

    def action_create_task(self):
        """Create a new task linked to this contact."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Task',
            'res_model': 'project.task',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.id,
            },
        }


class ProjectTask(models.Model):
    _inherit = 'project.task'

    def action_open_related_contact(self):
        """Redirect to Related Contact Form."""
        self.ensure_one()
        if self.partner_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'res.partner',
                'res_id': self.partner_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
