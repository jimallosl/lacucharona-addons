from odoo import api, fields, models, _
from odoo.exceptions import UserError

class LccMenuBuilderWizard(models.TransientModel):
    _name = "lcc.menu.builder.wizard"
    _description = "Asistente de construcción de menú"

    template_id = fields.Many2one("lcc.menu.template", required=True)
    order_id = fields.Many2one("sale.order", string="Pedido", required=True)

    line_ids = fields.One2many("lcc.menu.builder.line", "wizard_id", string="Selecciones")

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        template = self.env["lcc.menu.template"].browse(self.env.context.get("default_template_id"))
        order = self.env["sale.order"].browse(self.env.context.get("default_order_id"))
        if not template or not order:
            return vals
        line_vals = []
        warehouse = template.warehouse_id or order.website_id.warehouse_id or self.env["stock.warehouse"].search([], limit=1)
        wh_ctx = {"warehouse": warehouse.id} if warehouse else {}
        for tl in template.category_lines:
            candidates = tl.product_ids.with_context(**wh_ctx).filtered(lambda p: p.qty_available >= tl.min_stock and p.sale_ok)
            line_vals.append((0, 0, {
                "category": tl.category,
                "min_qty": tl.min_qty,
                "max_qty": tl.max_qty,
                "candidate_ids": [(6, 0, candidates.ids)],
                "show_allergens": tl.show_allergens,
            }))
        vals.update({"line_ids": line_vals})
        return vals

    def action_confirm(self):
        self.ensure_one()
        order = self.order_id
        template = self.template_id

        # Línea principal del menú (precio por tarifa)
        menu_product = template.product_id
        price = order.pricelist_id._get_product_price(menu_product, 1.0, order.partner_id) if hasattr(order.pricelist_id, "_get_product_price") else menu_product.lst_price
        parent_line = self.env["sale.order.line"].create({
            "order_id": order.id,
            "product_id": menu_product.id,
            "product_uom_qty": 1.0,
            "price_unit": price,
            "name": menu_product.get_product_multiline_description_sale(),
        })

        # Crear hijos a 0 €, permitiendo 0 selecciones por categoría
        for l in self.line_ids:
            if l.max_qty and len(l.selection_ids) > l.max_qty:
                raise UserError(_("Máximo %s en %s") % (l.max_qty, dict(l._fields["category"].selection).get(l.category)))
            for prod in l.selection_ids:
                self.env["sale.order.line"].create({
                    "order_id": order.id,
                    "product_id": prod.id,
                    "product_uom_qty": 1.0,
                    "price_unit": 0.0,
                    "discount": 0.0,
                    "name": prod.get_product_multiline_description_sale(),
                    "lcc_is_menu_component": True,
                    "lcc_menu_parent_id": parent_line.id,
                    "lcc_menu_category": l.category,
                })
                self.env["lcc.menu.history"].sudo().bump(order.partner_id, prod, l.category)
        return {"type": "ir.actions.act_window_close"}

class LccMenuBuilderLine(models.TransientModel):
    _name = "lcc.menu.builder.line"
    _description = "Selección por categoría"

    wizard_id = fields.Many2one("lcc.menu.builder.wizard", required=True, ondelete="cascade")
    category = fields.Selection([
        ("primero", "Primero"),
        ("segundo", "Segundo"),
        ("guarnicion", "Guarnición"),
        ("postre", "Postre"),
        ("pan", "Pan"),
    ], required=True)

    min_qty = fields.Integer(default=0)
    max_qty = fields.Integer(default=1)
    candidate_ids = fields.Many2many("product.product", string="Candidatos (en stock)")
    selection_ids = fields.Many2many("product.product", string="Elegidos")
    show_allergens = fields.Boolean(default=True)
