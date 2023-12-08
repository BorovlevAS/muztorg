# -*- coding: utf-8 -*-

# Part of Openauto
# See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StockReservation(models.TransientModel):
    _name = "stock.reservation"

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        readonly=True,
    )
    reservation_line_ids = fields.One2many(
        'stock.reservation.line',
        'reservation_id',
        string='Reservation Line',
    )
    user_ids = fields.Many2many(
        'res.users',
        string='Email Notification',
    )


    def action_create_reservation(self):
        self.ensure_one()
        custome_reservtion_obj = self.env['stock.move.reservation']
        location_obj = self.env['stock.location']
        picking_type_obj = self.env['stock.picking.type']
        move_id_generated = False
        mail_context = []

        for line in self.reservation_line_ids:
            if line.stock_reservation_qty > 0.0 and line.product_qty >= line.stock_reservation_qty:
                order_line_reserve_qty = line.order_line_id.stock_reserved_qty
                order_line_reserve_qty += line.stock_reservation_qty

                if line.order_line_id.product_uom_qty >= order_line_reserve_qty:
                    picking_type_id = picking_type_obj.search([
                        ('warehouse_id', '=', self.sale_order_id.warehouse_id.id),
                        ('code', '=', 'outgoing')],
                        limit=1
                    )
                    location_id = picking_type_id.default_location_src_id
                    # location_dest_id = self.env.ref("odoo_stock_reservation.stock_dest_location_reservation")
                    location_dest_id = self.env['stock.location'].search([
                        ('is_stock_location_reservation', '=', True),
                        ('company_id', '=', self.sale_order_id.company_id.id)], limit=1)

                    reserv_move_id = custome_reservtion_obj.create({
                        'name': self.sale_order_id.name,
                        'custome_so_line_id': line.order_line_id.id,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.stock_reservation_qty,
                        'product_uom': line.uom_id.id,
                        'location_id': location_id.id,
                        'location_dest_id': location_dest_id.id,
                        'custome_sale_order_id': self.sale_order_id.id,
                        'reserv_request_date': fields.Datetime.now(),
                        'reserv_resquest_user_id': self.env.uid,
                    })

                    if reserv_move_id:
                        line.order_line_id.stock_reserved_qty += line.stock_reservation_qty
                        self.sale_order_id.is_stock_reserv_created = True
                        mail_context.append({
                            'name': reserv_move_id.reserv_code,
                            'product_id': reserv_move_id.product_id,
                            'reserved_qty': reserv_move_id.product_uom_qty,
                        })
                        reserv_move_id.move_id._action_confirm()
                        move_id_generated = True
                    line.product_id.write({'is_reservation': True, 'reserver_id': self.env.user.id})
                else:
                    raise ValidationError("All the quantities are reserved")
            # else:
            #     raise ValidationError("Quantity is less then 0.0 or reserved quantity more then Order Quantity")

        if self.user_ids and move_id_generated:
            partner_lst = [(4, user.partner_id.id) for user in self.user_ids]
            email_template_id = self.env.ref("odoo_stock_reservation.email_template_stock_reservation1")
            ctx = self._context.copy()
            ctx.update({'stock_reservation_ctx': mail_context})
            if email_template_id:
                email_template_id.with_context(ctx).send_mail(
                    self.sale_order_id.id, email_values={'recipient_ids': partner_lst})


class StockReservationLine(models.TransientModel):
    _name = "stock.reservation.line"

    reservation_id = fields.Many2one(
        'stock.reservation',
        string='Reservation',
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        related="reservation_id.sale_order_id",
        store=True,
    )
    order_line_id = fields.Many2one(
        'sale.order.line',
        string='Sale Order Line',
        required=True,
        ondelete='cascade',
        domain=lambda self: [
            ('order_id', '=', self._context.get('current_sale_order_id'))],
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
    )
    product_qty = fields.Float(
        string="Quantity",
    )
    stock_reservation_qty = fields.Float(
        string="Reservation Quantity",
        required=True,
    )
    uom_id = fields.Many2one(
        #        'product.uom',
        'uom.uom',
        string="UOM",
    )

    @api.onchange("order_line_id")
    def _onchange_order_line_id(self):
        # T5087
        # if self.order_line_id.is_reservation:
        #     raise ValidationError('This product is already reservation...')
        # T5087
        self.product_id = self.order_line_id.product_id.id
        self.product_qty = self.order_line_id.product_uom_qty
        self.uom_id = self.order_line_id.product_uom.id
