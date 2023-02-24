# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Partner(models.Model):
    _inherit = "res.partner"

    biko_contact_person_id = fields.Many2one(
        comodel_name="res.partner",
        string="Contact person",
    )

    biko_recipient_id = fields.Many2one(
        comodel_name="res.partner",
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

    biko_parent_id = fields.Many2one("res.partner")

    biko_delivery_address_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="res_partner_delivery_address_rel",
        column1="biko_parent_id",
        column2="biko_delivery_address_ids",
        string="Delivery addresses",
    )
