from odoo import api, fields, models

class LccMenuHistory(models.Model):
    _name = "lcc.menu.history"
    _description = "Historial de elecciones de menú por partner/empleado"
    _order = "write_date desc"

    partner_id = fields.Many2one("res.partner", required=True, index=True)
    product_id = fields.Many2one("product.product", required=True, index=True)
    category = fields.Char()
    times = fields.Integer(default=1)

    @api.model
    def bump(self, partner, product, category):
        rec = self.search([
            ("partner_id", "=", partner.id),
            ("product_id", "=", product.id),
            ("category", "=", category),
        ], limit=1)
        if rec:
            rec.times += 1
        else:
            self.create({
                "partner_id": partner.id,
                "product_id": product.id,
                "category": category,
                "times": 1,
            })
