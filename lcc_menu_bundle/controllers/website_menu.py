from odoo import http
from odoo.http import request

class LccWebsiteMenu(http.Controller):

    @http.route(['/menu/<int:template_id>'], type='http', auth="public", website=True)
    def lcc_menu_page(self, template_id, **kw):
        template = request.env["lcc.menu.template"].sudo().browse(template_id)
        if not template or not template.allow_portal:
            return request.not_found()
        order = request.website.sale_get_order(force_create=True)
        wiz = request.env["lcc.menu.builder.wizard"].with_context(
            default_template_id=template.id,
            default_order_id=order.id,
        ).sudo().create({})
        return request.render("lcc_menu_bundle.website_menu_builder", {
            "template": template,
            "wizard": wiz,
        })

    @http.route(['/menu/submit/<int:wizard_id>'], type='http', auth="public", methods=['POST'], website=True, csrf=True)
    def lcc_menu_submit(self, wizard_id, **post):
        wiz = request.env["lcc.menu.builder.wizard"].sudo().browse(wizard_id)
        if not wiz:
            return request.not_found()
        form = request.httprequest.form
        for line in wiz.line_ids:
            key = f"cat_{line.id}"
            ids = [int(x) for x in form.getlist(key)] if hasattr(form, 'getlist') else []
            if ids:
                prods = request.env["product.product"].sudo().browse(ids)
                line.selection_ids = [(6, 0, prods.ids)]
        wiz.action_confirm()
        return request.redirect("/shop/cart")
