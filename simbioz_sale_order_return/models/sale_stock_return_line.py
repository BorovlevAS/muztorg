from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class SaleStockReturnLine(models.Model):
    _name = "sale.stock.return.line"
    _description = "Sale stock return line"
    _check_company_auto = True

    sale_stock_return_id = fields.Many2one(
        comodel_name="sale.stock.return",
        string="Sale stock return (nnt)",
        required=True,
        ondelete="cascade",
        check_company=True,
        copy=False,
    )

    sale_order_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Sale Order Line (nnt)",
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        related="sale_stock_return_id.company_id",
        string="Company (nnt)",
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="sale_stock_return_id.currency_id",
        string="Currency (nnt)",
    )

    product_id = fields.Many2one(
        comodel_name="product.product",
        related="sale_order_line_id.product_id",
        string="Product",
        ondelete="restrict",
        check_company=True,
    )
    product_template_id = fields.Many2one(
        "product.template",
        string="Product Template",
        related="product_id.product_tmpl_id",
    )
    name = fields.Text(
        string="Description",
        related="sale_order_line_id.name",
    )
    quantity_return = fields.Float(
        string="Quantity",
        required=True,
        default=0.0,
    )

    product_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
        related="sale_order_line_id.product_uom",
    )
    qty_invoiced = fields.Float(
        related="sale_order_line_id.qty_invoiced",
        string="Invoiced Qty",
    )
    qty_delivered = fields.Float(
        related="sale_order_line_id.qty_delivered",
        string="Delivered Qty",
    )

    price_unit = fields.Float(
        "Unit Price",
        digits="Product Price",
        related="sale_order_line_id.price_unit",
    )

    price_subtotal = fields.Monetary(
        compute="_compute_amount",
        string="Subtotal",
        readonly=True,
        store=True,
    )
    price_tax = fields.Float(
        compute="_compute_amount",
        string="Total Tax",
        readonly=True,
        store=True,
    )
    price_total = fields.Monetary(
        compute="_compute_amount",
        string="Total",
        readonly=True,
        store=True,
    )

    tax_id = fields.Many2many(
        comodel_name="account.tax",
        string="Taxes",
        related="sale_order_line_id.tax_id",
    )

    discount = fields.Float(
        string="Discount (%)",
        digits="Discount",
        related="sale_order_line_id.discount",
    )

    discount_total = fields.Monetary(
        compute="_compute_amount", string="Discount Subtotal", store=True
    )
    price_subtotal_no_discount = fields.Monetary(
        compute="_compute_amount", string="Subtotal Without Discount", store=True
    )
    price_total_no_discount = fields.Monetary(
        compute="_compute_amount", string="Total Without Discount", store=True
    )

    @api.depends("quantity_return")
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(
                price,
                line.sale_stock_return_id.currency_id,
                line.quantity_return,
                product=line.product_id,
                partner=line.sale_stock_return_id.partner_id,
            )

            if not line.discount:
                price_total_no_discount = taxes["total_included"]
                price_subtotal_no_discount = taxes["total_excluded"]
                discount_total = 0
            else:
                price = line.price_unit
                taxes = line.tax_id.compute_all(
                    price,
                    line.sale_stock_return_id.currency_id,
                    line.quantity_return,
                    product=line.product_id,
                    partner=line.sale_stock_return_id.partner_id,
                )

                price_total_no_discount = taxes["total_included"]
                price_subtotal_no_discount = taxes["total_excluded"]
                discount_total = price_total_no_discount - line.price_total

            line.update(
                {
                    "price_tax": sum(
                        t.get("amount", 0.0) for t in taxes.get("taxes", [])
                    ),
                    "price_total": taxes["total_included"],
                    "price_subtotal": taxes["total_excluded"],
                    "discount_total": discount_total,
                    "price_subtotal_no_discount": price_subtotal_no_discount,
                    "price_total_no_discount": price_total_no_discount,
                }
            )

    def _check_before_return(self):
        failed_lines = []
        for line in self:
            if not line.quantity_return:
                failed_lines.append(line.name)

        if failed_lines:
            raise UserError(
                _(
                    "The following lines have no quantity to return:\n %(failed_lines)s",
                    failed_lines="\n".join(failed_lines),
                )
            )
        return True

    def _get_moves_domain(self):
        domain = [
            ("state", "=", "done"),
            ("origin_returned_move_id", "=", False),
            ("qty_returnable", ">", 0),
            ("product_id", "=", self.product_id.id),
            (
                "picking_id.partner_id",
                "child_of",
                self.sale_stock_return_id.partner_id.commercial_partner_id.id,
            ),
            ("location_dest_id", "=", self.sale_stock_return_id.partner_location_id.id),
            (
                "sale_line_id",
                "=",
                self.sale_order_line_id.id,
            ),
        ]

        return domain

    def _get_returnable_move_ids(self):
        """Gets returnable stock.moves for the given request conditions

        :returns: a dict with request lines as keys containing a list of tuples
                  with qty returnable for a given move as the move itself
        :rtype: dictionary
        """
        moves_for_return = {}
        stock_move_obj = self.env["stock.move"]
        # Avoid lines with quantity to 0.0
        for line in self.filtered("quantity_return"):
            moves_for_return[line] = []
            precision = line.product_uom_id.rounding
            moves = stock_move_obj.search(
                line._get_moves_domain(), order="date asc, id desc"
            )
            qty_to_complete = line.quantity_return
            for move in moves:
                qty_returned = 0
                return_moves = move.returned_move_ids.filtered(
                    lambda x: x.state == "done"
                )
                # Don't count already returned
                if return_moves:
                    qty_returned = sum(
                        return_moves.mapped("move_line_ids").mapped("qty_done")
                    )
                quantity_done = sum(move.mapped("move_line_ids").mapped("qty_done"))
                qty_remaining = quantity_done - qty_returned
                # We add the move to the list if there are units that haven't
                # been returned
                if float_compare(qty_remaining, 0.0, precision_rounding=precision) > 0:
                    qty_to_return = min(qty_to_complete, qty_remaining)
                    moves_for_return[line] += [(qty_to_return, move)]
                    qty_to_complete -= qty_to_return
                if float_is_zero(qty_to_complete, precision_rounding=precision):
                    break
        return moves_for_return

    def _get_acc_returnable_ids(self):
        """Gets returnable account.moves for the given request conditions

        :returns: a dict with request lines as keys containing a list of dict
                  with qty returnable for a given move as the move itself
        :rtype: dictionary
        """
        moves_for_return = {}
        # Avoid lines with quantity to 0.0
        for line in self.filtered("quantity_return"):
            # AML : qty
            moves_for_return[line] = {}
            precision = line.product_uom_id.rounding
            moves = line.sale_order_line_id.invoice_lines.filtered(
                lambda x: x.parent_state == "posted"
            )
            for move in moves:
                acc_move = move.move_id
                qty = move.quantity
                if acc_move.move_type == "out_refund":
                    qty = -qty
                    acc_move = acc_move.reversed_entry_id
                if moves_for_return[line].get(acc_move):
                    moves_for_return[line][acc_move] += qty
                else:
                    moves_for_return[line][acc_move] = qty

        moves_to_create = {}
        for line, move_data in moves_for_return.items():
            qty_to_complete = line.quantity_return
            precision = line.product_uom_id.rounding
            for move, qty_remaining in move_data.items():
                if float_compare(qty_remaining, 0.0, precision_rounding=precision) > 0:
                    qty_to_return = min(qty_to_complete, qty_remaining)

                    if not moves_to_create.get(move):
                        moves_to_create[move] = {}

                    if moves_to_create.get(line):
                        moves_to_create[move][line] += qty_to_return
                    else:
                        moves_to_create[move][line] = qty_to_return

                    qty_to_complete -= qty_to_return
                if float_is_zero(qty_to_complete, precision_rounding=precision):
                    break

        return moves_to_create

    def _prepare_account_move_line_vals(self, **optional_values):
        res = {
            "name": self.name,
            "product_id": self.product_id.id,
            "product_uom_id": self.product_uom_id.id,
            "quantity": min(self.quantity_return, self.qty_invoiced),
            "discount": self.discount,
            "price_unit": self.price_unit,
            "tax_ids": [(6, 0, self.tax_id.ids)],
            "sale_line_ids": [(4, self.sale_order_line_id.id)],
        }
        if optional_values:
            res.update(optional_values)
        return res
