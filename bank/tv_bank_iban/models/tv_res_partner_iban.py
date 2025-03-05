# -*- coding: utf-8 -*-
from odoo.addons.base_iban.models.res_partner_bank import pretty_iban

def custom_pretty_iban(iban):
    """ Override pretty_iban to return IBAN without spaces """
    print("//////////////pretty?????????")
    try:
        validate_iban(iban)
    except ValidationError:
        pass
    return iban  # Just return the IBAN without spaces

# Monkey patch the global function
import odoo.addons.base_iban.models.res_partner_bank
odoo.addons.base_iban.models.res_partner_bank.pretty_iban = custom_pretty_iban