# -*- coding: utf-8 -*-
from odoo import http

class OpainCustom(http.Controller):
    @http.route('/opain_custom/opain_custom/', auth='public')
    def index(self, **kw):
        pos_obj = http.request.env['pos.session'].sudo()
        pos_2 = pos_obj.browse(2)
        pos_2._on_close_pos_session()

        return "Hello, world"

