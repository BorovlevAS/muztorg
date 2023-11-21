from odoo import _, api, fields, models


class ResPartnerNP(models.Model):
    _inherit = "res.partner"

    np_delivery_address = fields.Boolean(string="Address for Nova Poshta")
    np_name = fields.Char("Name")
    np_ref = fields.Char("Ref")
    np_city = fields.Many2one("delivery_novaposhta.cities_list", string="City")
    np_street = fields.Many2one(
        "delivery_novaposhta.streets_list",
        string="Street",
        domain="[('city_id', '=', np_city)]",
    )
    np_type = fields.Many2one(
        "delivery_novaposhta.types_of_counterparties",
        string="NP Type",
        compute="_compute_np_type",
    )
    np_service_type = fields.Selection(
        [("Doors", _("Address")), ("Warehouse", _("Warehouse"))],
        string="Service type",
        default="Warehouse",
    )
    np_ownership = fields.Many2one(
        "delivery_novaposhta.ownership_forms_list", string="NP Ownership"
    )
    np_warehouse = fields.Many2one(
        "delivery_novaposhta.warehouse",
        string="NP warehouse",
        domain="[('city_id', '=', np_city)]",
    )
    house = fields.Char("House number")
    flat = fields.Char("Flat")

    @api.depends("company_type")
    def _compute_np_type(self):
        street_env = self.env["delivery_novaposhta.types_of_counterparties"]
        organization = street_env.search([("ref", "=", "Organization")], limit=1)
        private_person = street_env.search([("ref", "=", "PrivatePerson")], limit=1)
        if organization and private_person:
            for r in self:
                if r.company_type == "person":
                    r.np_type = private_person
                elif r.company_type == "company":
                    r.np_type = organization

    # def set_vals_np(self, vals):
    #     # не понял я, что это за функция. Закомментирую ее, чтобы не мешалась
    #     fields_list = ["street", "city"]
    #     for field in fields_list:
    #         f = "np_%s" % field
    #         if vals.get(field) and not vals.get(f):
    #             model = eval("self[0]." + f)
    #             val = model.search([("name", "=", vals.get(field))], limit=1)
    #             vals[f] = val.id if val else False
    #     return vals


class AddresShipingNP(models.Model):
    _name = "delivery_novaposhta.address"

    city = fields.Many2one("delivery_novaposhta.cities_list", string="City")
    city_ref = fields.Char(compute="_compute_city_ref", help="Technical field")
    warehouse = fields.Many2one(
        "delivery_novaposhta.warehouse",
        domain="[('cityref', '=', city_ref)]",
        string="Warehouse",
    )
    streets = fields.Many2one("delivery_novaposhta.streets_list", string="Street")
    recipient_house = fields.Char(string="Recipient House")
    recipient_flat = fields.Integer(string="Recipient Flat")
    partner_id = fields.Many2one("res.partner")

    @api.depends("city")
    def _compute_city_ref(self):
        """Техническое поле, нужно для доменов"""
        for record in self:
            record.city_ref = record.city.ref
