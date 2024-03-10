from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import frozendict


class SaleStockReturn(models.Model):
    _name = "sale.stock.return"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "portal.mixin",
    ]
    _description = "Sale stock return"
    _check_company_auto = True

    _rec_name = "name"
    _order = "date DESC, name DESC"

    operation_type = fields.Selection(
        [
            ("financial_return", "Financial return"),
            ("stock_return", "Stock return"),
            ("full_return", "Full return"),
        ],
        string="Operation Type",
        required=True,
        default="full_return",
    )
    name = fields.Char(
        string="Name",
        default="/",
        required=True,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        required=True,
        related="sale_order_id.currency_id",
    )
    date = fields.Date(
        string="Date",
        default=fields.Date.context_today,
        required=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        required=True,
        check_company=True,
    )
    is_partner_contract_mandatory = fields.Boolean(
        related="partner_id.uavat_account_analytic_settlements"
    )

    contract_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Contract",
        domain="[('is_contract','=',True), ('contract_type', '=', 'purchase'), ('partner_id', '=', partner_id)]",
        check_company=True,
    )

    note = fields.Text(string="Note")

    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale order",
        required=True,
        domain="[('id', 'in', allowed_sale_order_ids)]",
        check_company=True,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Responsible",
        default=lambda self: self.env.user,
        required=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
    )

    allowed_sale_order_ids = fields.One2many(
        comodel_name="sale.order",
        compute="_compute_allowed_order_ids",
        string="Allowed Sale Orders (nnt)",
        check_company=True,
    )

    line_ids = fields.One2many(
        comodel_name="sale.stock.return.line",
        inverse_name="sale_stock_return_id",
        string="Lines",
        auto_join=True,
    )

    amount_untaxed = fields.Monetary(
        string="Untaxed Amount",
        store=True,
        readonly=True,
        compute="_compute_amount_all",
        tracking=5,
    )

    amount_tax = fields.Monetary(
        string="Taxes",
        store=True,
        readonly=True,
        compute="_compute_amount_all",
    )
    amount_total = fields.Monetary(
        string="Total",
        store=True,
        readonly=True,
        compute="_compute_amount_all",
        tracking=4,
    )

    discount_total = fields.Monetary(
        compute="_compute_discount_total",
        string="Discount Subtotal",
        currency_field="currency_id",
        store=True,
    )
    price_subtotal_no_discount = fields.Monetary(
        compute="_compute_discount_total",
        string="Subtotal Without Discount",
        currency_field="currency_id",
        store=True,
    )
    price_total_no_discount = fields.Monetary(
        compute="_compute_discount_total",
        string="Total Without Discount",
        currency_field="currency_id",
        store=True,
    )

    account_move_ids = fields.One2many(
        comodel_name="account.move",
        inverse_name="sale_stock_return_id",
        string="Account moves (nnt)",
    )
    stock_picking_ids = fields.One2many(
        comodel_name="stock.picking",
        inverse_name="sale_stock_return_id",
        string="Stock pickings (nnt)",
    )

    location_id = fields.Many2one(
        comodel_name="stock.location",
        domain="[('usage','=','internal')]",
        string="Location",
        required=True,
    )
    partner_location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Partner Location (nnt)",
        related="partner_id.property_stock_customer",
    )

    @api.depends("company_id", "state", "partner_id")
    def _compute_allowed_order_ids(self):
        for record in self:
            domain = [
                ("company_id", "=", record.company_id.id),
                ("order_partner_id", "=", record.partner_id.id),
                "|",
                ("qty_delivered", ">", 0),
                ("qty_invoiced", ">", record.partner_id.id),
            ]

            record.allowed_sale_order_ids = (
                self.env["sale.order.line"].search(domain).mapped("order_id")
            )

    @api.depends("line_ids.price_total")
    def _compute_amount_all(self):
        """
        Compute the total amounts of the rr.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update(
                {
                    "amount_untaxed": amount_untaxed,
                    "amount_tax": amount_tax,
                    "amount_total": amount_untaxed + amount_tax,
                }
            )

    @api.depends(
        "line_ids.discount_total",
        "line_ids.price_subtotal_no_discount",
        "line_ids.price_total_no_discount",
    )
    def _compute_discount_total(self):
        for order in self:
            discount_total = sum(order.line_ids.mapped("discount_total"))
            price_subtotal_no_discount = sum(
                order.line_ids.mapped("price_subtotal_no_discount")
            )
            price_total_no_discount = sum(
                order.line_ids.mapped("price_total_no_discount")
            )
            order.update(
                {
                    "discount_total": discount_total,
                    "price_subtotal_no_discount": price_subtotal_no_discount,
                    "price_total_no_discount": price_total_no_discount,
                }
            )

    @api.onchange("sale_order_id")
    def onchange_sale_order_id(self):
        for record in self:
            record.location_id = record.sale_order_id.warehouse_id.lot_stock_id.id

    def _prepare_move_default_values(self, line, qty, move):
        """Extend this method to add values to return move"""
        vals = {
            "product_id": line.product_id.id,
            "product_uom_qty": qty,
            "product_uom": line.product_uom_id.id,
            "state": "draft",
            "location_id": line.sale_stock_return_id.partner_location_id.id,
            "location_dest_id": line.sale_stock_return_id.location_id.id,
            "origin_returned_move_id": move.id,
            "to_refund": True,
            "procure_method": "make_to_stock",
        }
        return vals

    def _prepare_return_picking(self, picking_dict, moves):
        """Extend to add more values if needed"""
        picking_type = self.env["stock.picking.type"].browse(
            picking_dict.get("picking_type_id")
        )
        return_picking_type = (
            picking_type.return_picking_type_id or picking_type.return_picking_type_id
        )
        picking_dict.update(
            {
                "move_lines": [(6, 0, moves.ids)],
                "move_line_ids": [(6, 0, moves.mapped("move_line_ids").ids)],
                "picking_type_id": return_picking_type.id,
                "state": "draft",
                "origin": _("Return of %s", picking_dict.get("origin")),
                "location_id": self.partner_location_id.id,
                "location_dest_id": self.location_id.id,
                "sale_stock_return_id": self.id,
            }
        )
        return picking_dict

    def _create_picking(self, pickings, picking_moves):
        """Create return pickings with the proper moves"""
        return_pickings = self.env["stock.picking"]
        for picking in pickings:
            picking_dict = picking.copy_data(
                {
                    "origin": picking.name,
                    "printed": False,
                    "ttn": False,
                }
            )[0]
            moves = picking_moves.filtered(
                lambda move, picking=picking: move.origin_returned_move_id.picking_id
                == picking
            )
            new_picking = return_pickings.create(
                self._prepare_return_picking(picking_dict, moves)
            )
            new_picking.message_post_with_view(
                "mail.message_origin_link",
                values={"self": new_picking, "origin": picking},
                subtype_id=self.env.ref("mail.mt_note").id,
            )
            return_pickings += new_picking
        return return_pickings

    def generate_stock_moves(self):
        returnable_moves = self.line_ids._get_returnable_move_ids()
        return_moves = self.env["stock.move"]
        done_moves = {}
        for line in returnable_moves.keys():
            for qty, move in returnable_moves[line]:
                if move not in done_moves:
                    vals = self._prepare_move_default_values(line, qty, move)
                    return_move = move.copy(vals)
                else:
                    return_move = done_moves[move]
                    return_move.product_uom_qty += qty
                done_moves.setdefault(move, self.env["stock.move"])
                done_moves[move] += return_move
                return_move._action_confirm()
                return_move._action_assign()
                return_moves += return_move
        # Finish move traceability
        for move in return_moves:
            vals = {}
            origin_move = move.origin_returned_move_id
            move_orig_to_link = origin_move.move_dest_ids.mapped("returned_move_ids")
            move_dest_to_link = origin_move.move_orig_ids.mapped("returned_move_ids")
            vals["move_orig_ids"] = [(4, m.id) for m in move_orig_to_link | origin_move]
            vals["move_dest_ids"] = [(4, m.id) for m in move_dest_to_link]
            move.write(vals)
        # Make return pickings and link to the proper moves.
        origin_pickings = return_moves.mapped("origin_returned_move_id.picking_id")
        self.stock_picking_ids = self._create_picking(origin_pickings, return_moves)

    def _prepare_account_move_vals(self):
        reverse_date = self.date
        journal = (
            self.env["account.move"]
            .with_context(default_move_type="out_invoice")
            ._get_default_journal()
        )
        if not journal:
            raise UserError(
                _(
                    "Please define an accounting sales journal for the company %(company_name)s (%(company_id)s).",
                    company_name=self.company_id.name,
                    company_id=self.company_id.id,
                )
            )

        invoice_vals = {
            "invoice_date": reverse_date,
            "date": reverse_date,
            "move_type": "out_refund",
            "narration": self.note,
            "currency_id": self.currency_id.id,
            "campaign_id": self.sale_order_id.campaign_id.id,
            "medium_id": self.sale_order_id.medium_id.id,
            "source_id": self.sale_order_id.source_id.id,
            "user_id": self.user_id.id,
            "invoice_user_id": self.user_id.id,
            "team_id": self.sale_order_id.team_id.id,
            "partner_id": self.partner_id.id,
            "partner_shipping_id": self.partner_id.id,
            "journal_id": journal.id,  # company comes from the journal
            "invoice_origin": self.name,
            "invoice_line_ids": [],
            "company_id": self.company_id.id,
        }

        return invoice_vals

    def generate_account_moves(self):
        moves_for_return = self.line_ids._get_acc_returnable_ids()
        created_moves = []

        for move, lines in moves_for_return.items():
            invoice_vals = self._prepare_account_move_vals()
            invoice_vals["reversed_entry_id"] = move.id
            invoice_item_sequence = 0
            invoice_line_vals = []
            for line, qty in lines.items():
                invoice_line_vals.append(
                    (
                        0,
                        0,
                        line._prepare_account_move_line_vals(
                            sequence=invoice_item_sequence, quantity=qty
                        ),
                    )
                )
                invoice_item_sequence += 1
            invoice_vals["invoice_line_ids"] += invoice_line_vals
            move = self.env["account.move"].sudo().create(invoice_vals)
            move._post()
            # reconcile

            lines_to_reconcile = move.line_ids.filtered(
                lambda line: line.account_id.reconcile and not line.reconciled
            )
            lines_to_reconcile += move.reversed_entry_id.line_ids.filtered(
                lambda move: move.account_id.reconcile and not move.reconciled
            )
            lines_to_reconcile.sudo().reconcile()
            created_moves.append(move.id)

        self.sudo().write({"account_move_ids": [(6, 0, created_moves)]})

    def action_validate(self):
        self.ensure_one()
        new_context = frozendict(
            {k: v for k, v in self.env.context.items() if not k.startswith("default_")}
        )
        this = self.with_context(new_context)  # pylint: disable=W8121
        this.line_ids._check_before_return()
        if this.operation_type in ["stock_return", "full_return"]:
            this.generate_stock_moves()
        if this.operation_type in ["financial_return", "full_return"]:
            this.generate_account_moves()
        this.write({"state": "done"})

    def action_set_cancel(self):
        cancel_warning = self._show_cancel_wizard()
        if cancel_warning:
            return {
                "name": _("Cancel Return Order"),
                "view_mode": "form",
                "res_model": "sale.return.cancel",
                "view_id": self.env.ref(
                    "simbioz_sale_order_return.return_order_cancel_view_form"
                ).id,
                "type": "ir.actions.act_window",
                "context": {"default_order_id": self.id},
                "target": "new",
            }
        return self._action_cancel()

    def _action_cancel(self):
        self.account_move_ids.button_draft()
        self.account_move_ids.button_cancel()
        self.stock_picking_ids.filtered(lambda p: p.state != "done").action_cancel()
        self.write({"state": "cancel"})

    def _show_cancel_wizard(self):
        if not self._context.get("disable_cancel_warning"):
            return True
        return False

    def action_back_to_draft(self):
        self.write({"state": "draft"})

    def generate_action(self, field_name, module_name, action_name, form_name):
        record_ids = self.mapped(field_name)
        action = self.env["ir.actions.actions"]._for_xml_id(
            f"{module_name}.{action_name}"
        )
        if len(record_ids) > 1:
            action["domain"] = [("id", "in", record_ids.ids)]
        elif len(record_ids) == 1:
            form_view = [
                (
                    self.env.ref(f"{module_name}.{form_name}").id,
                    "form",
                )
            ]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = record_ids.id
        else:
            action = {"type": "ir.actions.act_window_close"}

        return action

    def action_view_invoice(self):
        return self.generate_action(
            "account_move_ids",
            "account",
            "action_move_out_refund_type",
            "view_move_form",
        )

    def action_view_stock_moves(self):
        return self.generate_action(
            "stock_picking_ids", "stock", "action_picking_tree_all", "view_picking_form"
        )

    def action_view_sale_order(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "view_type": "form",
            "view_mode": "form",
            "target": "current",
            "res_id": self.sale_order_id.id,
            "context": dict(self._context),
        }

    def action_fill_products(self):
        for record in self:
            new_lines = [(5, 0, 0)]

            for order_line in record.sale_order_id.order_line.filtered(
                lambda line: line.product_id.type in ["product", "consu"]
                and not line.display_type
                and (line.qty_delivered or line.qty_invoiced)
            ):
                order_line_vals = order_line._prepare_return_order_line_vals()
                new_lines.append((0, 0, order_line_vals))

            record.write({"line_ids": new_lines})

    def action_add_products(self):
        self.ensure_one()

        move_lines = self.sale_order_id.order_line.filtered(
            lambda line: line.product_id.type in ["product", "consu"]
            and not line.display_type
            and (line.qty_delivered or line.qty_invoiced)
        )

        new_lines = []
        for line in move_lines:
            new_lines.append(
                (
                    0,
                    0,
                    {
                        "sale_order_line_id": line.id,
                        "currency_id": self.sale_order_id.currency_id.id,
                    },
                )
            )

        wizard = self.env["add.so.lines.wizard"].create(
            {
                "return_order_id": self.id,
                "domain_sale_line_ids": new_lines,
            }
        )

        view = self.env.ref("simbioz_sale_order_return.add_so_lines_wizard_view_form")

        return {
            "name": _("Add SO Lines"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "add.so.lines.wizard",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": wizard.id,
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "company_id" in vals:
                self = self.with_company(vals["company_id"])
            if vals.get("name", "/") == "/":
                seq_date = None
                if "create_date" in vals:
                    seq_date = fields.Datetime.context_timestamp(
                        self, fields.Datetime.to_datetime(vals["date"])
                    )
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code(
                        "sale.return.order.seq", sequence_date=seq_date
                    )
                    or "/"
                )

        result = super().create(vals_list)
        return result
