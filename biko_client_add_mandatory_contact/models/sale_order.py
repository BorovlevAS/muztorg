import json

from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    biko_dealer_id = fields.Many2one("res.partner", string="Dealer")

    filter_biko_contact_person_ids = fields.Many2many(
        related="partner_id.biko_contact_person_ids",
    )
    biko_contact_person_id = fields.Many2one(
        "res.partner",
        string="Contact person",
    )

    biko_contact_person_type = fields.Selection(
        [("dealer", "Linked to the partner"), ("person", "Any contact from list")],
        string="Contact filter",
        default="person",
    )

    filter_biko_recipient_ids = fields.Many2many(
        related="partner_id.biko_recipient_ids",
    )
    biko_recipient_id = fields.Many2one(
        "res.partner",
        string="Recipient person",
    )

    biko_recipient_type = fields.Selection(
        [("dealer", "Linked to the partner"), ("person", "Any contact from list")],
        string="Recipient filter",
        default="person",
    )

    partner_id_domain = fields.Char(compute="_compute_partner_id_domain", readonly=True, store=False)
    biko_recepient_domain = fields.Char(
        compute="_compute_biko_recepient_domain",
        readonly=True,
        store=False,
    )

    biko_contact_domain = fields.Char(
        compute="_compute_biko_contact_domain",
        readonly=True,
        store=False,
    )

    @api.depends("biko_dealer_id")
    def _compute_partner_id_domain(self):
        for rec in self:
            if rec.biko_dealer_id:
                rec.partner_id_domain = json.dumps(
                    [
                        ("parent_id", "=", rec.biko_dealer_id.id),
                        "|",
                        ("company_id", "=", False),
                        ("company_id", "=", rec.company_id.id),
                    ]
                )

            else:
                rec.partner_id_domain = json.dumps(
                    [
                        "|",
                        ("company_id", "=", False),
                        ("company_id", "=", rec.company_id.id),
                    ]
                )

    @api.depends("biko_recipient_type")
    def _compute_biko_recepient_domain(self):
        for rec in self:
            if rec.biko_recipient_type == "dealer":
                rec.biko_recepient_domain = json.dumps([("id", "in", rec.filter_biko_recipient_ids.ids)])
            else:
                rec.biko_recepient_domain = json.dumps([("id", "!=", False)])

    @api.depends("biko_contact_person_type")
    def _compute_biko_contact_domain(self):
        for rec in self:
            if rec.biko_contact_person_type == "dealer":
                rec.biko_contact_domain = json.dumps([("id", "in", rec.filter_biko_contact_person_ids.ids)])
            else:
                rec.biko_contact_domain = json.dumps([("id", "!=", False)])

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for rec in self:
            if rec.partner_id.biko_carrier_id:
                rec.carrier_id = rec.partner_id.biko_carrier_id
            rec.biko_recipient_type = "dealer" if rec.partner_id.is_company else "person"
            rec.biko_contact_person_type = "dealer" if rec.partner_id.is_company else "person"
