from odoo import _, fields, models


class AddPOLinesWizard(models.TransientModel):
    _name = "add.so.lines.wizard"
    _description = "Add SO Lines"
    _rec_name = "id"

    return_order_id = fields.Many2one(
        comodel_name="sale.stock.return",
        string="Return Order",
    )
    domain_sale_line_ids = fields.One2many(
        comodel_name="add.so.lines.wizard.line",
        inverse_name="add_so_lines_wizard_id",
        string="Domain Sale Order Lines",
    )
    sale_order_line_ids = fields.Many2many(
        comodel_name="add.so.lines.wizard.line",
        string="Sale Order Lines",
        domain="[('id', 'in', domain_sale_line_ids)]",
    )

    def action_add_so_lines(self):
        new_lines = []
        for line in self.sale_order_line_ids:
            new_line_vals = {
                "sale_order_line_id": line.sale_order_line_id.id,
                "sale_stock_return_id": self.return_order_id.id,
            }
            new_lines.append((0, 0, new_line_vals))
        return self.return_order_id.write({"line_ids": new_lines})


class AddPOLinesWizardLine(models.TransientModel):
    _name = "add.so.lines.wizard.line"

    add_so_lines_wizard_id = fields.Many2one(comodel_name="add.po.lines.wizard")
    sale_order_line_id = fields.Many2one(comodel_name="sale.order.line")

    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency")

    product_id = fields.Many2one(
        comodel_name="product.product",
        related="sale_order_line_id.product_id",
        string="Product",
    )

    product_description = fields.Text(
        related="sale_order_line_id.name", string="Product Name (nnt.)"
    )
    qty_invoiced = fields.Float(
        related="sale_order_line_id.qty_invoiced", string="Product Qty (nnt.)"
    )
    product_uom = fields.Many2one(
        related="sale_order_line_id.product_uom", string="Product UOM (nnt.)"
    )
    qty_delivered = fields.Float(
        related="sale_order_line_id.qty_delivered", string="Product UOM Qty (nnt.)"
    )
    # with taxes
    price_total = fields.Monetary(
        related="sale_order_line_id.price_total", string="Total Price (nnt.)"
    )
    # w/o taxes
    price_subtotal = fields.Monetary(
        related="sale_order_line_id.price_subtotal", string="Subtotal Price (nnt.)"
    )

    def name_get(self):
        res = []
        for record in self:
            name = _(
                "%(prod_descr)s: [Inv. qty: %(inv_qty)s] - [Del. qty: %(del_qty)s] - [UoM: %(uom)s]  - [Sum w/o taxes: %(subtotal)s] - [Sum with taxes: %(total)s]",
                prod_descr=record.product_description,
                inv_qty=record.qty_invoiced,
                del_qty=record.qty_delivered,
                uom=record.product_uom.name,
                subtotal=record.price_subtotal,
                total=record.price_total,
            )
            res.append((record.id, name))

        return res
