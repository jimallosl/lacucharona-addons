from odoo import fields, models

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    lcc_is_menu_component = fields.Boolean(default=False)
    lcc_menu_parent_id = fields.Many2one("sale.order.line", string="Línea menú padre")
    lcc_menu_category = fields.Selection([
        ("primero", "Primero"),
        ("segundo", "Segundo"),
        ("guarnicion", "Guarnición"),
        ("postre", "Postre"),
        ("pan", "Pan"),
    ], string="Categoría bundle")
