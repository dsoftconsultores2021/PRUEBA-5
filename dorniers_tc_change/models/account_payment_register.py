# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    currency_tc = fields.Float(string='Tipo de Cambio',digits = (12,3),default=1.0)
    is_payment_in_me = fields.Boolean(string="Es Pago en Moneda Extranjera", compute="compute_is_payment_in_me", store=True)
    is_special_tc = fields.Boolean(string='Editar Tipo Cambio', help='Permitir editar el Tipo de Cambio por el usuario')

    @api.depends('currency_id')
    def compute_is_payment_in_me(self):
        for rec in self:
            #Obtenemos True o False si la moneda es extranjera
            rec.is_payment_in_me = rec.currency_id != rec.company_id.currency_id
            #rec.is_payment_in_me = False
            #if rec.currency_id and rec.currency_id != rec.company_id.currency_id:
            #    rec.is_payment_in_me = True
            #else:
            #    rec.is_payment_in_me = False

    @api.onchange('payment_date', 'currency_id', 'partner_id')
    def get_currency_tc(self):
        v_inverse_company_rate = 1
        if self.currency_id != self.company_id.currency_id:
            excha = self.env['res.currency.rate'].search([
                ('currency_id', '=', self.currency_id.id), ('name', '=', self.payment_date), ('company_id','=', self.company_id.id)
                ], limit=1)
            if excha:
                v_inverse_company_rate = excha.inverse_company_rate
            else:
                excha = self.env['res.currency.rate'].search([
                    ('currency_id', '=', self.currency_id.id), ('name', '<=', self.payment_date), ('company_id','=', self.company_id.id)
                    ], order='name desc', limit=1)
                v_inverse_company_rate = excha.inverse_company_rate if excha else 1

        self.currency_tc = v_inverse_company_rate


    def _create_payments(self):
        payments = super(AccountPaymentRegister, self)._create_payments()

        v_inverse_company_rate = 1
        if self.currency_id != self.company_currency_id and self.is_special_tc == False:
            excha = self.env['res.currency.rate'].search([
                ('currency_id', '=', self.currency_id.id), ('name', '=', self.payment_date), ('company_id','=', self.company_id.id)
                ], limit=1)
            if excha:
                v_inverse_company_rate = excha.inverse_company_rate
            else:
                excha = self.env['res.currency.rate'].search([
                    ('currency_id', '=', self.currency_id.id), ('name', '<=', self.payment_date), ('company_id','=', self.company_id.id)
                    ], order='name desc', limit=1)
                v_inverse_company_rate = excha.inverse_company_rate if excha else 1

        if self.is_special_tc != False:
            v_inverse_company_rate = self.currency_tc
        for payment in payments:
            payment.currency_tc = v_inverse_company_rate

        return payments

    def _create_payment_vals_from_wizard(self):
        res = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        res['currency_tc'] = self.currency_tc
        res['is_payment_in_me'] = self.is_payment_in_me
        res['is_special_tc'] = self.is_special_tc
        return res

    def _create_payment_vals_from_batch(self, batch_result):
        res = super(AccountPaymentRegister, self)._create_payment_vals_from_batch(batch_result)
        res['currency_tc'] = self.currency_tc
        res['is_payment_in_me'] = self.is_payment_in_me
        res['is_special_tc'] = self.is_special_tc
        return res