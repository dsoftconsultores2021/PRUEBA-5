# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    currency_tc= fields.Float(string='Tipo de Cambio',digits = (12,3), default=1.0)
    is_special_tc = fields.Boolean(string='Editar Tipo Cambio', help='Permitir editar el Tipo de Cambio por el usuario')
    is_payment_in_me = fields.Boolean(string="Es Pago en Moneda Extranjera",compute="compute_is_payment_in_me", store=True)
    
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

    @api.onchange('date', 'currency_id', 'partner_id')
    def get_currency_tc(self):
        v_inverse_company_rate = 1
        if self.currency_id != self.company_id.currency_id:
            excha = self.env['res.currency.rate'].search([
                ('currency_id', '=', self.currency_id.id), ('name', '=', self.date),
                ('company_id','=', self.company_id.id)
                ], limit=1)
            if excha:
                inverse_company_rate = excha.inverse_company_rate
            else:
                excha = self.env['res.currency.rate'].search([
                    ('currency_id', '=', self.currency_id.id), ('name', '<=', self.date),
                    ('company_id','=', self.company_id.id)
                    ], order='name desc', limit=1)
                v_inverse_company_rate = excha.inverse_company_rate if excha else 1

        self.currency_tc = v_inverse_company_rate


    #############################################################################
    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :param write_off_line_vals: Optional dictionary to create a write-off account.move.line easily containing:
            * amount:       The amount to be added to the counterpart amount.
            * name:         The label to set on the line.
            * account_id:   The account on which create the write-off.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}

        if not self.outstanding_account_id:
            raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                self.payment_method_line_id.name, self.journal_id.display_name))

        # Compute amounts.
        write_off_amount_currency = write_off_line_vals.get('amount', 0.0)

        if self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = self.amount
        elif self.payment_type == 'outbound':
            # Send money.
            liquidity_amount_currency = -self.amount
            write_off_amount_currency *= -1
        else:
            liquidity_amount_currency = write_off_amount_currency = 0.0

        """write_off_balance = self.currency_id._convert(
            write_off_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        liquidity_balance = self.currency_id._convert(
            liquidity_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )"""
        #####################################################################
        if self.is_special_tc and self.currency_tc > 0 and\
            self.currency_id and self.company_id.currency_id and self.company_id.currency_id != self.currency_id :

            write_off_balance = self.currency_id.with_context(default_pen_rate=self.currency_tc)._convert(
            write_off_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
            )

            liquidity_balance = self.currency_id.with_context(default_pen_rate=self.currency_tc)._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
        else:

            write_off_balance = self.currency_id._convert(
                write_off_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
        ############################################################################3
        counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
        counterpart_balance = -liquidity_balance - write_off_balance
        currency_id = self.currency_id.id

        if self.is_internal_transfer:
            if self.payment_type == 'inbound':
                liquidity_line_name = _('Transfer to %s', self.journal_id.name)
            else: # payment.payment_type == 'outbound':
                liquidity_line_name = _('Transfer from %s', self.journal_id.name)
        else:
            liquidity_line_name = self.payment_reference

        # Compute a default label to set on the journal items.

        payment_display_name = self._prepare_payment_display_name()

        default_line_name = self.env['account.move.line']._get_default_line_name(
            _("Internal Transfer") if self.is_internal_transfer else payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
            self.amount,
            self.currency_id,
            self.date,
            partner=self.partner_id,
        )

        line_vals_list = [
            # Liquidity line.
            {
                'name': liquidity_line_name or default_line_name,
                'date_maturity': self.date,
                'amount_currency': liquidity_amount_currency,
                'currency_id': currency_id,
                'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.outstanding_account_id.id,
            },
            # Receivable / Payable.
            {
                'name': self.payment_reference or default_line_name,
                'date_maturity': self.date,
                'amount_currency': counterpart_amount_currency,
                'currency_id': currency_id,
                'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.destination_account_id.id,
            },
        ]
        if not self.currency_id.is_zero(write_off_amount_currency):
            # Write-off line.
            line_vals_list.append({
                'name': write_off_line_vals.get('name') or default_line_name,
                'amount_currency': write_off_amount_currency,
                'currency_id': currency_id,
                'debit': write_off_balance if write_off_balance > 0.0 else 0.0,
                'credit': -write_off_balance if write_off_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': write_off_line_vals.get('account_id'),
            })
        return line_vals_list