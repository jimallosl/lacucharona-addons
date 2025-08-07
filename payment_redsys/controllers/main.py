# payment_redsys/controllers/main.py

from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class RedsysController(http.Controller):

    @http.route(['/payment/redsys/return'], type='http', auth='public', csrf=False)
    def redsys_return(self, **post):
        """ Página a la que se redirige al usuario después del pago """
        _logger.info("Redsys return: %s", post)
        return request.render("payment_redsys.redsys_return_page", {})

    @http.route(['/payment/redsys/notify'], type='http', auth='public', csrf=False)
    def redsys_notify(self, **post):
        """ Notificación directa de Redsys """
        _logger.info("Redsys notify: %s", post)
        # Aquí debes validar la firma, actualizar el estado del pedido, etc.
        return 'OK'
