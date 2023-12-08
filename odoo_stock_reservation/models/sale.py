# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_stock_reservation_order = fields.Boolean(
        string="Apply Stock Reservation?",
        copy=False,
    )
    stock_move_ids = fields.One2many(
        "stock.move.reservation",
        "custome_sale_order_id",
        string="Stock Reservations",
        copy=False,
    )

    is_stock_reserv_created = fields.Boolean(
        string="Is Stock Created",
        copy=False,
    )

    def action_confirm(self):
        for order in self:
            order_line = order.order_line
            stock_move_reservation_ids = self.env["stock.move.reservation"].search(
                [
                    ("custome_so_line_id", "in", order_line.ids),
                    ("state", "!=", "cancel"),
                ]
            )
            if stock_move_reservation_ids:
                # raise ValidationError("Please Cancel Reserved Stock")
                self.action_cancel_stock_reservation()
        return super().action_confirm()

    def action_create_stock_reservation(self):
        self.ensure_one()
        return {
            "name": _("Stock Reservation"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "stock.reservation",
            "view_id": self.env.ref(
                "odoo_stock_reservation.wiz_stock_reservation_view"
            ).id,
            "type": "ir.actions.act_window",
            "context": {
                "default_sale_order_id": self.id,
                "current_sale_order_id": self.id,
            },
            "target": "new",
        }

    def action_cancel_stock_reservation(self):
        self.ensure_one()
        order_line_ids = self.order_line
        stock_move_reservation_ids = self.env["stock.move.reservation"].search(
            [
                ("custome_so_line_id", "in", order_line_ids.ids),
                ("state", "!=", "cancel"),
            ]
        )
        stock_move_ids = self.env["stock.move"]
        for move_res in stock_move_reservation_ids:
            stock_move_ids += move_res.move_id
        if stock_move_ids:
            result = stock_move_ids._action_cancel()
            if result:
                order_line_ids.write(
                    {
                        "stock_reserved_qty": 0.0,
                    }
                )
                # ****************************************
                # 'product_id.is_reservation': False
                order_line_ids.product_id.write(
                    {"is_reservation": False, "reserver_id": False}
                )
                # ****************************************
                self.is_stock_reserv_created = False
            return {
                "type": "ir.actions.client",
                "tag": "reload",
            }
        else:
            if not self._context.get("is_unlink_reserved_stock"):
                return {
                    "type": "ir.actions.client",
                    "tag": "reload",
                }
                # raise ValidationError("No any stock reservation records found.")

    def action_cancel(self):
        self.ensure_one()
        order_line_ids = self.order_line
        stock_move_reservation_ids = self.env["stock.move.reservation"].search(
            [
                ("custome_so_line_id", "in", order_line_ids.ids),
            ]
        )
        if stock_move_reservation_ids:
            ctx = self._context.copy()
            ctx.update({"is_unlink_reserved_stock": True})
            self.with_context(ctx).action_cancel_stock_reservation()
            #            self.action_cancel_stock_reservation()
            stock_move_reservation_ids.unlink()
        return super().action_cancel()

    def action_view_reserved_stock(self):
        self.ensure_one()
        action = (
            self.env.ref("odoo_stock_reservation.action_stock_move_reserv_product")
            .sudo()
            .read()[0]
        )
        action["domain"] = [("id", "in", self.stock_move_ids.ids)]
        return action

    def schedule_action_cancel_reservation(self):
        # ICPSudo = self.env['ir.config_parameter'].sudo()
        # nb_days = ICPSudo.get_param('odoo_stock_reservation.nb_days')
        # self.ensure_one()
        nb_days = 0
        # _logger.critical('********RESERVATIONS*********')

        if self.env["number.days.reservation"].search([])[0]:
            nb_days = self.env["number.days.reservation"].search([])[0].nb_days
        # _logger.critical(nb_days)
        # _logger.critical(datetime.datetime.now())
        # _logger.critical('--------------------------------------')
        # date_obj = fields.Date.today() - relativedelta(days=int(nb_days))
        date_obj = (fields.datetime.now()) - relativedelta(hours=int(nb_days * 24))
        # _logger.critical(date_obj)
        # sales = self.env['sale.order'].search([('validity_date', '=', date_obj)])
        # reservations = self.env['stock.move.reservation'].search([('reserv_request_date', '=', date_obj),
        #                                                           ('state', '!=', 'cancel')])
        reservations = self.env["stock.move.reservation"].search(
            [("reserv_request_date", "<=", date_obj), ("state", "!=", "cancel")]
        )
        # _logger.critical(reservations)
        for reserve in reservations:
            # reserve.write({'state': 'cancel'})
            reserve.custome_sale_order_id.action_cancel_stock_reservation()
        # for sale in sales:
        #     sale.action_cancel_stock_reservation()

    # def _create_invoices(self, grouped=False, final=False, date=None):
    #     for line in self.order_line:
    #         if line.is_reservation:
    #             raise ValidationError("Can't create invoice because in this sale there is line reserved")
    #     return super(SaleOrder, self)._create_invoices()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    stock_reserved_qty = fields.Float(string="Stock Reserved Quantity")

    is_reservation = fields.Boolean(related="product_id.is_reservation")
    reserver_id = fields.Many2one(
        related="product_id.reserver_id", string="Reserved By"
    )

    def write(self, vals):
        if "product_id" in vals:
            for rec in self:
                stock_move_reservation_ids = self.env["stock.move.reservation"].search(
                    [("custome_so_line_id", "=", rec.id), ("state", "!=", "cancel")]
                )
                stock_move_ids = self.env["stock.move"]
                for move_res in stock_move_reservation_ids:
                    stock_move_ids += move_res.move_id
                if stock_move_ids:
                    result = stock_move_ids._action_cancel()
                    if result:
                        vals.update(stock_reserved_qty=0.0)
        #                        vals.update(is_stock_reserv_created=True)
        return super().write(vals)

    def unlink(self):
        for rec in self:
            stock = self.env["stock.move.reservation"].search(
                [("custome_so_line_id", "=", rec.id)]
            )
            stock_res_move_ids = stock.mapped("move_id")
            stock_res_move_ids._action_cancel()
            stock.unlink()
        return super().unlink()

    # T5087 net ponimaniya dlya chego eta ficha nuzhno bolshe vremeni
    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     for line in self:
    #         if line.product_id.is_reservation:
    #             product = line.product_id.name
    #             reserver = line.product_id.reserver_id.name
    #             line.unlink()
    #             raise ValidationError(
    #                 _('The product %s is already reserved by %s, Please contact him to cancel the reservation to proceed.') % (
    #                     product, reserver))
    # T5087
