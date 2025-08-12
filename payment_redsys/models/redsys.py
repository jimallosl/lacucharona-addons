# payment_redsys/models/redsys.py

from odoo import fields, models, api
import base64
import hashlib
import hmac
import json
import logging

_logger = logging.getLogger(__name__)


class PaymentAcquirerRedsys(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('redsys', 'Redsys')], ondelete={'redsys': 'set default'})
    redsys_merchant_code = fields.Char("Merchant Code", required_if_provider='redsys')
    redsys_secret_key = fields.Char("Secret Key", required_if_provider='redsys')
    redsys_terminal = fields.Char("Terminal", default='1', required_if_provider='redsys')

    def _get_redsys_urls(self):
    """
    Regla:
      - Terminal '999' => entorno de PRUEBAS (sis-t)
      - Cualquier otro => PRODUCCIÓN
    Ignoramos self.environment para evitar confusiones.
    """
    self.ensure_one()
    TEST_URL = 'https://sis-t.redsys.es:25443/sis/realizarPago'
    PROD_URL = 'https://sis.redsys.es/sis/realizarPago'

    terminal = (self.redsys_terminal or '').strip()
    return TEST_URL if terminal == '999' else PROD_URL

    def redsys_generate_sign(self, parameters, secret_key):
        order = parameters.get("Ds_Order")
        merchant_parameters = base64.b64encode(json.dumps(parameters).encode()).decode()
        key = base64.b64decode(secret_key)
        key = hmac.new(key, order.encode(), hashlib.sha256).digest()
        signature = base64.b64encode(hmac.new(key, merchant_parameters.encode(), hashlib.sha256).digest()).decode()
        return merchant_parameters, signature

    def _get_feature_support(self):
        res = super()._get_feature_support()
        res['authorize'].append('redsys')
        res['tokenize'].append('redsys')
        return res

    def redsys_generate_sign(self, parameters, secret_key):
    order = parameters.get("Ds_Order") or parameters.get("order")  # <—
    merchant_parameters = base64.b64encode(json.dumps(parameters).encode()).decode()
    key = base64.b64decode(secret_key)
    key = hmac.new(key, order.encode(), hashlib.sha256).digest()
    signature = base64.b64encode(hmac.new(key, merchant_parameters.encode(), hashlib.sha256).digest()).decode()
    return merchant_parameters, signature

