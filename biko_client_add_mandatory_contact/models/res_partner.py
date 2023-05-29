# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Partner(models.Model):
    _inherit = "res.partner"

    # служебное поле для связки m2m записей
    biko_parent_id = fields.Many2one("res.partner")

    biko_contact_person_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="res_partner_contact_person_rel",
        column1="biko_parent_id",
        column2="biko_contact_person_id",
        string="Contact person",
    )

    is_filled_contact_person = fields.Boolean(compute="_compute_is_filled_contact_person")

    biko_recipient_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="res_partner_recepient_rel",
        column1="biko_parent_id",
        column2="biko_recipient_ids",
        string="Recipient person",
    )

    biko_buyer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Buyer person",
    )

    biko_payer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Payer person",
    )

    biko_delivery_address_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="res_partner_delivery_address_rel",
        column1="biko_parent_id",
        column2="biko_delivery_address_ids",
        string="Delivery addresses",
    )

    is_group = fields.Boolean(string="Group of companies", default=False)

    enterprise_code = fields.Char(
        copy=False,
    )

    biko_carrier_id = fields.Many2one("delivery.carrier", string="Delivery carrier")

    def _compute_is_filled_contact_person(self):
        for rec in self:
            rec.is_filled_contact_person = bool(rec.biko_contact_person_ids)

    @api.depends("vat", "company_id", "enterprise_code")
    def _compute_same_vat_partner_id(self):
        for partner in self:
            # use _origin to deal with onchange()
            partner_id = partner._origin.id
            # active_test = False because if a partner has been deactivated you still want to raise the error,
            # so that you can reactivate it instead of creating a new one, which would loose its history.
            Partner = self.with_context(active_test=False).sudo()
            domain = [
                ("enterprise_code", "=", partner.enterprise_code),
                ("company_id", "in", [False, partner.company_id.id]),
            ]
            if partner_id:
                domain += [
                    ("id", "!=", partner_id),
                    "!",
                    ("id", "child_of", partner_id),
                ]
            partner.same_vat_partner_id = (
                bool(partner.enterprise_code) and not partner.parent_id and Partner.search(domain, limit=1)
            )

    @api.constrains("enterprise_code")
    def _check_enterprise_code(self):
        for record in self:
            if record.company_type == "person":
                # skip for contact
                continue
            if not record.country_id or record.country_id.code != "UA":
                # skip for foreign company
                continue
            if not record.enterprise_code:
                continue

            Partner = self.with_context(active_test=False).sudo()

            domain = [
                ("enterprise_code", "=", record.enterprise_code),
                ("company_id", "in", [False, record.company_id.id]),
            ]
            partner_id = record._origin.id

            if partner_id:
                domain += [("id", "!=", partner_id)]

            companies = Partner.search(domain).mapped("name")

            if not companies:
                continue

            message = _("Clients with EDRPOU {} is already exists\n").format(record.enterprise_code)

            for name in companies:
                message += name + "\n"

            raise ValidationError(message)
