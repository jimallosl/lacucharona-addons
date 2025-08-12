# payment_redsys/models/redsys.py

from odoo import fields, models, api
import base64
import hashlib
import hmac
import json
import logging
import time

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

    def redsys_form_generate_values(self, values):
        """
        Prepara los valores del render para Redsys:
        - Importe en céntimos (string).
        - ORDER solo con dígitos (4–12). También sobreescribimos 'reference'
          para que el builder de MerchantParameters use el numérico.
        """
        self.ensure_one()

        # --- Importe en céntimos (entero, como string) ---
        amount_eur = float(values.get('amount') or 0.0)
        amount_cents = str(int(round(amount_eur * 100)))  # 0.20 € => "20"

        # --- Nº de pedido: solo dígitos (Redsys exige 4–12 dígitos) ---
        ref = str(values.get('reference') or '')
        order_digits = ''.join(ch for ch in ref if ch.isdigit())[-12:] or str(int(time.time()))

        tx_values = dict(values)
        tx_values.update({
            'merchant_code': self.redsys_merchant_code,
            'terminal': self.redsys_terminal,
            'signature_version': "HMAC_SHA256_V1",
            'currency': '978',              # EUR
            'transaction_type': '0',
            'url': self._get_redsys_urls(),
            # claves usadas más adelante por el builder/plantilla:
            'amount': amount_cents,         # FORZAMOS CÉNTIMOS (string)
            'order': order_digits,          # FORZAMOS SOLO DÍGITOS
        })

        # Forzar que el builder que use 'reference' también sea numérico
        tx_values['reference'] = order_digits

        # Opcional: exponer explícitamente las claves Merchant para otros builders
        tx_values['Ds_Merchant_Amount'] = amount_cents
        tx_values['Ds_Merchant_Currency'] = '978'
        tx_values['Ds_Merchant_Order'] = order_digits
        tx_values['Ds_Merchant_MerchantCode'] = self.redsys_merchant_code
        tx_values['Ds_Merchant_Terminal'] = self.redsys_terminal
        tx_values['Ds_Merchant_TransactionType'] = '0'

        _logger.warning(
            "REDSYS DEBUG form_values: amount_eur=%s amount_cents=%s order=%s url=%s",
            values.get('amount'), tx_values.get('amount'), tx_values.get('order'), tx_values.get('url')
        )

        return tx_values

   from Crypto.Cipher import DES3
from Crypto.Util.Padding import pad

def redsys_generate_sign(self, parameters, secret_key):
    """
    Firma Redsys (HMAC_SHA256_V1):
    1) key_base = base64.b64decode(secret_key)
    2) key_derived = 3DES-CBC(key_base, iv=0) sobre Ds_Merchant_Order (con padding)
    3) signature = base64( HMAC-SHA256( key_derived, merchant_parameters ) )
    """
    # 1) Merchant parameters JSON base64
    merchant_parameters = base64.b64encode(json.dumps(parameters).encode()).decode()

    # 2) ORDER: preferimos Ds_Merchant_Order (numérico), luego alternativas
    order = (
        parameters.get("Ds_Merchant_Order")
        or parameters.get("DS_MERCHANT_ORDER")
        or parameters.get("Ds_Order")
        or parameters.get("order")
        or ""
    )

    # 3) Derivar clave con 3DES-CBC IV=0 a partir del ORDER
    key_base = base64.b_


    def _get_feature_support(self):
        res = super()._get_feature_support()
        res['authorize'].append('redsys')
        res['tokenize'].append('redsys')
        return res


