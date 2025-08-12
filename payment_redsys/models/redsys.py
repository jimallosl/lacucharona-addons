# payment_redsys/models/redsys.py

from odoo import fields, models
import base64
import hashlib
import hmac
import json
import logging
import time

from Crypto.Cipher import DES3
from Crypto.Util.Padding import pad

_logger = logging.getLogger(__name__)


class PaymentProviderRedsys(models.Model):
    """ Odoo 16/17/18 usan payment.provider (no payment.acquirer). """
    _inherit = 'payment.provider'

    # Registrar el proveedor
    code = fields.Selection(selection_add=[('redsys', 'Redsys')], ondelete={'redsys': 'set default'})

    # Credenciales Redsys
    redsys_merchant_code = fields.Char("Merchant Code", required_if_provider='redsys')
    redsys_secret_key = fields.Char("Secret Key", required_if_provider='redsys')
    redsys_terminal = fields.Char("Terminal", default='1', required_if_provider='redsys')

    # URL según terminal (999 => test)
    def _redsys_get_api_url(self):
        self.ensure_one()
        TEST_URL = 'https://sis-t.redsys.es:25443/sis/realizarPago'
        PROD_URL = 'https://sis.redsys.es/sis/realizarPago'
        terminal = (self.redsys_terminal or '').strip()
        return TEST_URL if terminal == '999' else PROD_URL

    # Firma Redsys (3DES + HMAC-SHA256, url-safe)
    @staticmethod
    def _redsys_sign(merchant_parameters_b64: str, order: str, secret_key_b64: str) -> str:
        key_base = base64.b64decode(secret_key_b64)
        cipher = DES3.new(key_base, DES3.MODE_CBC, iv=b'\0' * 8)
        key_derived = cipher.encrypt(pad(order.encode(), 8))
        mac = hmac.new(key_derived, merchant_parameters_b64.encode(), hashlib.sha256).digest()
        return base64.b64encode(mac).decode().replace('+', '-').replace('/', '_')

    # Valores específicos para render (lo consume payment_transaction)
    def _get_specific_rendering_values(self, tx, processing_values):
        _logger.warning("REDSYS DEBUG >>> our provider hook is RUNNING (staging)")

        """Construye Ds_MerchantParameters, firma y URL."""
        self.ensure_one()
        assert self.code == 'redsys'

        # Importe en céntimos (string) y order solo dígitos (4–12)
        amount_cents = str(int(round((tx.amount or 0.0) * 100)))
        ref = str(tx.reference or '')
        order_digits = ''.join(ch for ch in ref if ch.isdigit())[-12:] or str(tx.id)

        params = {
            'Ds_Merchant_Amount': amount_cents,
            'Ds_Merchant_Currency': '978',
            'Ds_Merchant_Order': order_digits,
            'Ds_Merchant_MerchantCode': self.redsys_merchant_code or '',
            'Ds_Merchant_Terminal': (self.redsys_terminal or '1').strip(),
            'Ds_Merchant_TransactionType': '0',
            'Ds_Merchant_MerchantName': self.company_id.name or '',
            'Ds_Merchant_Titular': (self.company_id.name or '')[:60],
            'Ds_Merchant_UrlOK': tx.return_url,
            'Ds_Merchant_UrlKO': tx.return_url,
        }

        merchant_parameters_b64 = base64.b64encode(json.dumps(params).encode()).decode()
        signature = self._redsys_sign(merchant_parameters_b64, order_digits, self.redsys_secret_key or '')

        api_url = self._redsys_get_api_url()
        _logger.warning("REDSYS DEBUG: amount_cents=%s order=%s api_url=%s", amount_cents, order_digits, api_url)

        return {
            'Ds_MerchantParameters': merchant_parameters_b64,
            'Ds_SignatureVersion': 'HMAC_SHA256_V1',
            'Ds_Signature': signature,
            'api_url': api_url + '/',  # respeta cómo lo espera tu template
        }


