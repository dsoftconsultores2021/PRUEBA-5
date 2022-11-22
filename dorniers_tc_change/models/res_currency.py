# -*- encoding: utf-8 -*-
from odoo import api, fields, models, tools, _
import logging
_logger = logging.getLogger(__name__)

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):

        currency_rates = (from_currency + to_currency)._get_rates(company,date)
        _logger.info('\n\nCURRENCIE RATES\n\n')
        _logger.info(currency_rates)

        if self.env.context.get('default_pen_rate'):
            #res = currency_rates.get(company.currency_id.id)/(self.env.context.get('default_pen_rate'))
            res = self.env.context.get('default_pen_rate')

        else:
            res = currency_rates.get(to_currency.id)/currency_rates.get(from_currency.id)
        _logger.info('\n\nRES\n\n')
        _logger.info(res)
        return res