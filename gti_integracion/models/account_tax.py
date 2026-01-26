# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    tax_code = fields.Char(string="Código de Impuesto")
    codigo_Imp = fields.Selection(
        string="Código Tarifa",
        selection=[
            ('1', 'Tarifa 0% (exento)'),
            ('2', 'Tarifa reducida 1%'),
            ('3', 'Tarifa reducida 2%'),
            ('4', 'Tarifa reducida 4%'),
            ('5', 'Transitorio 0%'),
            ('6', 'Transitorio 4%'),
            ('7', 'Transitorio 8%'),
            ('8', 'Tarifa general 13%'),
        ],
        required=True,
        tracking=True,
    )