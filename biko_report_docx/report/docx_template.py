# from os.path import join as opj
from odoo import _, fields, models
from odoo.exceptions import UserError


class DocxTemplate(models.Model):
    _name = "biko.docx.template"

    name = fields.Char(string="Template Name", required=True)
    res_model = fields.Char(
        string="Resource Model",
        help="The database object this attachment will be attached to.",
    )
    fname = fields.Char(string="File Name")
    datas = fields.Binary(string="File Content")

    report_action_id = fields.Many2one(
        comodel_name="ir.actions.report",
        string="Report Action",
    )
    is_report_action = fields.Boolean()

    report_name = fields.Char()

    def add_report_menu(self):
        self.ensure_one()
        if not self.fname:
            raise UserError(_("No file content!"))
        # Create report action
        vals = {
            "name": self.name,
            "model": self.res_model,
            "report_type": "docx",
            "report_name": self.report_name,
            "report_file": self.fname,
            # "print_report_name": "(object._get_report_pf_filename())",
            "print_report_name": f"'{self.report_name} - %s' % (object.name).replace('/', '')",
            "binding_model_id": self.env["ir.model"]
            .search([("model", "=", self.res_model)])
            .id,
            "binding_type": "report",
            "binding_view_types": "form",
        }
        report_action = self.env["ir.actions.report"].create(vals)
        self.report_action_id = report_action

        self.is_report_action = True

    def remove_report_menu(self):
        self.ensure_one()
        if self.report_action_id:
            self.report_action_id.unlink()

        self.is_report_action = False
