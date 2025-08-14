from odoo import api, fields, models

LCC_CATEGORIES = [
    ("primero", "Primero"),
    ("segundo", "Segundo"),
    ("guarnicion", "Guarnición"),
    ("postre", "Postre"),
    ("pan", "Pan"),
]

class LccMenuTemplate(models.Model):
    _name = "lcc.menu.template"
    _description = "Plantilla de menú (reglas por empresa)"

    name = fields.Char(required=True)
    product_id = fields.Many2one("product.product", required=True, help="Producto 'Menú' principal (precio fijo por tarifa)")
    category_lines = fields.One2many("lcc.menu.template.line", "template_id", string="Categorías")
    company_ids = fields.Many2many("res.partner", string="Empresas asignadas")
    active = fields.Boolean(default=True)
    allow_portal = fields.Boolean(default=True, help="Permite usar este menú desde el portal")

    enforce_exact_choices = fields.Boolean(default=False, help="Si está activo, obliga a elegir exactamente el mínimo configurado")
    warehouse_id = fields.Many2one("stock.warehouse", help="Almacén para calcular disponibilidad (si vacío, usa el del website)")

class LccMenuTemplateLine(models.Model):
    _name = "lcc.menu.template.line"
    _description = "Categoría y platos permitidos en un menú"

    template_id = fields.Many2one("lcc.menu.template", required=True, ondelete="cascade")
    category = fields.Selection(LCC_CATEGORIES, required=True)
    product_ids = fields.Many2many("product.product", string="Platos permitidos")
    min_qty = fields.Integer(default=0)
    max_qty = fields.Integer(default=1)
    show_allergens = fields.Boolean(default=True, help="Mostrar botón de ingredientes/alérgenos")

    min_stock = fields.Float(default=1.0, help="Stock mínimo para mostrar el plato")

    @api.constrains("min_qty", "max_qty")
    def _check_qty(self):
        for r in self:
            if r.min_qty < 0 or r.max_qty < 0 or r.max_qty < r.min_qty:
                raise ValueError("Cantidades mín./máx. inválidas en la categoría %s" % r.category)
