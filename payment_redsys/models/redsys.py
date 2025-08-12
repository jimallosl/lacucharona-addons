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
    """Proveedor Redsys para payment.provider (Odoo 16/17/18)."""
    _inherit = 'payment.provider'

    # Registrar el proveedor
    code = fields.Selection(selection_add=[('redsys', 'Redsys')], ondelete={'redsys': 'set default'})

    # Credenciales Redsys
    redsys_merchant_code = fields.Char("Merchant Code", required_if_provider='redsys')
    redsys_secret_key = fields.Char("Secret Key", required_if_provider='redsys')  # en BASE64 (tal cual la da Redsys)
    redsys_terminal = fields.Char("Terminal", default='1', required_if_provider='redsys')

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _redsys_get_api_url(self):
        """Terminal '999' => entorno de pruebas (sis-t). Otro => producción."""
        self.ensure_one()
        TEST_URL = 'https://sis-t.redsys.es:25443/sis/realizarPago/'
        PROD_URL = 'https://sis.redsys.es/sis/realizarPago/'
        terminal = (self.redsys_terminal or '').strip()
        return TEST_URL if terminal == '999' else PROD_URL

    @staticmethod
    def _redsys_order_digits(reference: str, fallback: str) -> str:
        """
        Redsys exige ORDER numérico (4–12 dígitos). Extraemos dígitos del
        reference; si no hay, usamos fallback. Aseguramos rango 4–12.
        """
        digits = ''.join(ch for ch in (reference or '') if ch.isdigit())
        if not digits:
            digits = fallback
        # Nos quedamos con los últimos 12 dígitos y garantizamos mínimo de 4
        digits = digits[-12:]
        if len(digits) < 4:
            digits = digits.zfill(4)
        return digits

    @staticmethod
    def _redsys_sign(merchant_parameters_b64: str, order: str, secret_key_b64: str) -> str:
        """
        Firma Redsys (HMAC_SHA256_V1):
        1) key_base = base64(secret_key)
        2) key_derived = 3DES-CBC(IV=0) cifrando 'order' con padding a 8
        3) signature = base64( HMAC-SHA256( key_derived, merchant_parameters_b64 ) )
        """
        # 1) Clave base
        key_base = base64.b64decode(secret_key_b64)
        # Redsys tolera claves de 16 ó 24 bytes; si vienen 16, expandimos a 24
        if len(key_base) == 16:
            key_base = key_base + key_base[:8]
        # 2) Derivar clave con 3DES-CBC(IV=0)
        cipher = DES3.new(key_base, DES3.MODE_CBC, iv=b'\x00' * 8)
        key_derived = cipher.encrypt(pad(order.encode('ascii'), 8))
        # 3) HMAC-SHA256 y base64 estándar
        mac = hmac.new(key_derived, merchant_parameters_b64.encode('ascii'), hashlib.sha256).digest()
        return base64.b64encode(mac).decode('ascii')

    # -------------------------------------------------------------------------
    # Render
    # -------------------------------------------------------------------------

    def _get_specific_rendering_values(self, tx, processing_values):
        """
        Construye Ds_MerchantParameters, Ds_Signature y endpoint.
        Odoo fusiona lo devuelto con los 'processing_values' genéricos.
        """
        self.ensure_one()
        assert self.code == 'redsys'

        # Importe en CENTS (string)
        amount_cents = str(int(round((tx.amount or 0.0) * 100)))

        # ORDER numérico 4–12 dígitos
        # fallback: tx.id + epoch para evitar colisiones
        fallback = f"{tx.id}{int(time.time())}"
        order_digits = self._redsys_order_digits(tx.reference or '', fallback)

        # Parámetros Merchant
        params = {
            'Ds_Merchant_Amount': amount_cents,
            'Ds_Merchant_Currency': '978',
            'Ds_Merchant_Order': order_digits,
            'Ds_Merchant_MerchantCode': (self.redsys_merchant_code or '').strip(),
            'Ds_Merchant_Terminal': (self.redsys_terminal or '1').strip(),
            'Ds_Merchant_TransactionType': '0',
            # Opcionales pero útiles
            'Ds_Merchant_MerchantName': (self.company_id.name or '')[:45],
            'Ds_Merchant_Titular': (self.company_id.name or '')[:60],
            'Ds_Merchant_ProductDescription': (tx.reference or '')[:125],
            # Retornos
            'Ds_Merchant_UrlOK': tx.return_url,
            'Ds_Merchant_UrlKO': tx.return_url,
        }

        # JSON sin espacios + base64
        merchant_parameters_b64 = base64.b64encode(
            json.dumps(params, separators=(',', ':')).encode('utf-8')
        ).decode('ascii')

        # Firma
        signature = self._redsys_sign(merchant_parameters_b64, order_digits, (self.redsys_secret_key or '').strip())

        api_url = self._redsys_get_api_url()

        _logger.warning(
            "REDSYS DEBUG -> amount_cents=%s order=%s api_url=%s merchant=%s term=%s",
            amount_cents, order_digits, api_url, params['Ds_Merchant_MerchantCode'], params['Ds_Merchant_Terminal']
        )

        return {
            'Ds_MerchantParameters': merchant_parameters_b64,
            'Ds_SignatureVersion': 'HMAC_SHA256_V1',
            'Ds_Signature': signature,
            'api_url': api_url,  # tu template puede añadir el form action aquí
        }
