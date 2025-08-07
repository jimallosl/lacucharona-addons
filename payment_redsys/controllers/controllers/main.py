from odoo import http
from odoo.http import request

class RedsysController(http.Controller):

    @http.route(['/payment/redsys/return'], type='http', auth='public', csrf=False)
    def redsys_return(self, **post):
        # Aquí se manejará la respuesta del TPV Redsys
        return request.redirect('/payment/process')
