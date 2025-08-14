{
    "name": "LCC Menu Bundle",
    "version": "18.0.1.0",
    "summary": "Bundles de menús por categorías con stock real, ingredientes e historial.",
    "depends": [
        "sale_management",
        "website_sale",
        "stock",
        "mrp",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/menu_template_views.xml",
        "views/menu_builder_views.xml",
        "views/product_template_inherit.xml",
        "views/website_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": []
    },
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
