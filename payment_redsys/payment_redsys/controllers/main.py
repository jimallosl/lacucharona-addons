from odoo import http
from odoo.http import request

class RedsysController(http.Controller):
    @http.route(['/payment/redsys/return'], type='http', auth='none', csrf=False)
    def redsys_return(self, **post):
        return request.redirect('/payment/process')