from odoo import models, fields

class PaymentAcquirerRedsys(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('redsys', 'Redsys')])
    redsys_merchant_code = fields.Char(string="Merchant Code")
    redsys_secret_key = fields.Char(string="Secret Key")
    redsys_terminal = fields.Char(string="Terminal")
