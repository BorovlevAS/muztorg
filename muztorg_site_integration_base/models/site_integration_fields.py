from odoo import fields, models


class SiteIntegrationField(models.Model):
    _name = "site.integration.field"

    name = fields.Char()
    # setting_pickup_id = fields.Many2one(string="Pickup", comodel_name="delivery.carrier")
    # setting_nova_poshta_id = fields.Many2one(
    #     string="Nova poshta", comodel_name="delivery.carrier"
    # )
    # setting_warehouse_podol_id = fields.Many2one(
    #     string="Warehouse Podol", comodel_name="stock.warehouse"
    # )
    # model_id = fields.Many2one(
    #     comodel_name="ir.model", required=True, ondelete="cascade"
    # )
    # model_name = fields.Char(
    #     related="model_id.model",
    #     store=True,
    #     readonly=True,
    #     index=True,
    #     string="Model name",
    # )
    # model_reference = fields.Reference(
    #     # compute="_compute_origin_values",
    #     selection="_reference_models",
    #     # readonly=True
    # )
    # expression = fields.Char(required=True)
    # model = fields.Many2one(
    # #     string="Warehouse Podol",
    #     comodel_name="ir.model"
    # )
    ref_model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Ref Model",
        # help="Select model if you want to use it to create analytic tags, "
        # "each tag will have reference to the data record in that model.\n"
        # "For example, if you select Department (hr.department) then click "
        # "Create Tags button, tags will be created from each department "
        # " and also has resource_ref to the department record",
    )
    # filtered_field_ids = fields.Many2many(
    #     comodel_name="ir.model.fields",
    #     string="Filtered by fields",
    #     domain="[('model_id', '=', ref_model_id), ]",
    #     # ('ttype', '=', 'many2one')

    #     # help="Filtered listing tags by fields of this model, based on value "
    #     # "of selected analytic tags in working document",
    # )
    field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        domain="[('model_id', '=', ref_model_id), ]",
        required=True,
        readonly=True,
        ondelete="cascade",
    )

    # def _get_related_field(self):
    #     """Determine the chain of fields."""
    #     self.ensure_one()
    #     related = self.expression.split(".")
    #     target = self.env[self.model_name]
    #     for name in related:
    #         field = target._fields[name]
    #         target = target[name]
    #     return field

    # @api.constrains("model_id", "expression")
    # def _check_expression(self):
    #     for record in self:
    #         try:
    #             record._get_related_field()
    #         except KeyError:
    #             raise exceptions.ValidationError(_("Incorrect expression."))

    # @api.model
    # def _reference_models(self):
    #     models = self.env["ir.model"].search([])
    #     return [(model.model, model.name) for model in models]
