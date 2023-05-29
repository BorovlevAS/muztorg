from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    biko_dealer_id = fields.Many2one("res.partner", string="Dealer")
    partner_id = fields.Many2one(
        "res.partner",
        domain="""[
        '|', 
        ('company_id', '=', False), 
        ('company_id', '=', company_id), 
        ('parent_id', '=', biko_dealer_id),
        '!',
        (biko_dealer_id, '=?', False),
        ]
        """,
    )
    biko_contact_person_id = fields.Many2one("res.partner", string="Contact person")
    biko_recipient_id = fields.Many2one("res.partner", string="Recipient person")

    """
    дилер - может быть пустым - это всегда с типом компания
    покупатель от дилера или физлицо
    контактное лицо - от дилера или от физлица
    получатель - от дилера или от физлица
    адрес доставки - от дилера или от физлица
    """
