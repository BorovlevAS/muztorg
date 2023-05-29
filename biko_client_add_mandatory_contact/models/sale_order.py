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
        domain="[('id', 'in', filter_biko_contact_person_ids)]",
    )

    filter_biko_recipient_ids = fields.Many2many(
        related="partner_id.biko_recipient_ids",
    )
    biko_recipient_id = fields.Many2one(
        "res.partner",
        string="Recipient person",
        domain="[('id', 'in', filter_biko_recipient_ids)]",
    )

    partner_id_domain = fields.Char(compute="_compute_partner_id_domain", readonly=True, store=False)

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

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for rec in self:
            if rec.partner_id.biko_carrier_id:
                rec.carrier_id = rec.partner_id.biko_carrier_id

    """
    дилер - может быть пустым - это всегда с типом компания
    покупатель от дилера или физлицо
    контактное лицо - от дилера или от физлица
    получатель - от дилера или от физлица
    адрес доставки - от дилера или от физлица
    """
