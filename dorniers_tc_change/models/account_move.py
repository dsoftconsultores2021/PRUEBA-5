# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging
#_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_special_tc = fields.Boolean(string='Editar Tipo Cambio', help='Permitir editar el Tipo de Cambio por el usuario')
    currency_tc = fields.Float(string='Tipo de Cambio',digits = (12,3), default=1.0)
    is_invoice_in_me = fields.Boolean(string="Es Documento en Moneda Extranjera",compute="compute_is_invoice_in_me",store=True)
    invoice_date = fields.Date(default=fields.Date.context_today)

    """
    move_type:
    entry= Journal Entry / out_invoice=Customer Invoice / out_refund=Customer Credit Note
    in_invoice=Vendor Bill / in_refund= Vendor Credit Note
    out_receipt = Sales Receipt / in_receipt = Purchase Receipt
    """

    @api.depends('currency_id')
    def compute_is_invoice_in_me(self):
        for rec in self:
            #Obtenemos True o False si la moneda es extranjera
            #rec.is_invoice_in_me = rec.currency_id != rec.company_id.currency_id
            rec.is_invoice_in_me = False
            if rec.currency_id and rec.currency_id != rec.company_id.currency_id:
                rec.is_invoice_in_me = True
            else:
                rec.is_invoice_in_me = False

    #Obtener el Tipo de Cambio 
    def get_information_currency_tc(self):
        for rec in self:
            information_currency_tc = 1.0
            if rec.invoice_date or rec.date and not rec.is_special_tc and rec.currency_id and \
                rec.currency_id != rec.company_id.currency_id:
                #Comprobante de Cliente y Proveedor
                if rec.move_type in ['out_invoice','in_invoice'] :
                    currency_rate_id = self.env['res.currency.rate'].search([
                        ('name', '<=', rec.invoice_date),
                        ('company_id', '=', rec.company_id.id),
                        ('currency_id', '=', rec.currency_id.id)], order="name desc", limit=1)
                    if currency_rate_id:
                        information_currency_tc = currency_rate_id.inverse_company_rate
                #Nota de Credito de Cliente y Proveedor :: se usa TC de su comprobante original
                elif rec.move_type in ['in_refund','out_refund'] :
                    currency_rate_id = self.env['res.currency.rate'].search([
                        ('name', '<=', rec.reversed_entry_id.invoice_date),
                        ('company_id', '=', rec.company_id.id),
                        ('currency_id', '=', rec.reversed_entry_id.currency_id.id)], order="name desc", limit=1)
                    if currency_rate_id:
                        information_currency_tc = currency_rate_id.inverse_company_rate
                
                elif rec.move_type in ['entry'] :
                    currency_rate_id = self.env['res.currency.rate'].search([
                        ('name', '<=', rec.date),
                        ('company_id', '=', rec.company_id.id),
                        ('currency_id', '=', rec.currency_id.id)], order="name desc", limit=1)
                    if currency_rate_id:
                        information_currency_tc = currency_rate_id.inverse_company_rate
            else:
                information_currency_tc = rec.currency_tc

            return information_currency_tc


    @api.onchange('is_special_tc','currency_id','invoice_date','date','price_unit','tax_ids')
    def onchange_is_special_tc(self):
        self.ensure_one()
        #for rec in self:
        if not self.is_special_tc:
            self.currency_tc = self.get_information_currency_tc()
        for line in self.line_ids:
            line._onchange_amount_currency()
        self._recompute_dynamic_lines(recompute_tax_base_amount=True)
    ##########################################################################

    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        current_invoice_lines = self.line_ids.filtered(lambda line: not line.exclude_from_invoice_tab)
        others_lines = self.line_ids - current_invoice_lines
        if others_lines and current_invoice_lines - self.invoice_line_ids:
            others_lines[0].recompute_tax_line = True
        self.line_ids = others_lines + self.invoice_line_ids
        self._onchange_recompute_dynamic_lines()

    ###########################################################################
    """
    @api.onchange('date','invoice_date','currency_id')
    def _onchange_currency(self):
        for rec in self:
            if not rec.is_special_tc:
                super(AccountMove,self)._onchange_currency()

        for rec in self:
            if rec.move_type in ['in_invoice','in_refund'] and rec.currency_id != rec.company_id.currency_id and not rec.is_special_tc:
                if not rec.currency_id:
                    return
                if rec.is_invoice(include_receipts=True):
                    company_currency = rec.company_id.currency_id
                    has_foreign_currency = rec.currency_id and rec.currency_id != company_currency
                    for line in rec._get_lines_onchange_currency():
                        new_currency = has_foreign_currency and rec.currency_id
                        line.currency_id = new_currency
                        line._onchange_currency()
                else:
                    rec.line_ids._onchange_currency()

                rec._recompute_dynamic_lines(recompute_tax_base_amount=True)
    """
    ##########################################################################

    @api.onchange('currency_tc','is_special_tc','invoice_line_ids','invoice_line_ids.price_unit','invoice_line_ids.tax_ids')
    def onchange_currency_tc(self):
        for rec in self:
            for line in rec.line_ids:
                line._onchange_amount_currency()
            rec._recompute_dynamic_lines(recompute_tax_base_amount=True)


    #@api.onchange('invoice_line_ids.price_unit','invoice_line_ids.tax_ids')
    #def onchange_price_unit_tax_ids(self):
    #    for rec in self:
    #        rec.onchange_currency_tc()

    #@api.onchange('currency_id')
    #def onchange_currency_id(self):
    #    for rec in self:
    #        for line in rec.line_ids:

    #            line._onchange_amount_currency()

    ##########################################################################
    #@api.onchange('date')
    #def onchange_currency_tc(self):
    #    for rec in self:
    #        if rec.move_type == 'entry':
    #            for line in rec.line_ids:
    #                line._onchange_amount_currency()
    ##########################################################################

    @api.constrains('is_special_tc')
    def contrains_not_zero(self):
        if self.is_special_tc:
            if self.currency_tc <= 0.00:
                raise ValidationError(_('El tipo de Cambio no puede ser menor o igual que 0'))


    def _reverse_moves(self, default_values_list=None, cancel=False):
        if not default_values_list:
            default_values_list = [{} for move in self]
        for move, default_values in zip(self, default_values_list):
            default_values.update({
                'is_special_tc': True,
                'currency_tc': move.currency_tc,
            })
        reverse_moves = super()._reverse_moves(default_values_list=default_values_list, cancel=cancel)
        reverse_moves.onchange_currency_tc()
        return reverse_moves



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    currency_tc= fields.Float(related='move_id.currency_tc', string='Tipo de Cambio',
        digits = (12,3),store=True)
    is_special_tc = fields.Boolean(string='Tipo Cambio Personalizado', help='Se usó Tipo de Cambio personalizado por el usuario',
        related='move_id.is_special_tc')


    @api.onchange('amount_currency')
    def _onchange_amount_currency(self):
        super(AccountMoveLine,self)._onchange_amount_currency()
        for line in self:

            company = line.move_id.company_id
            company_currency = line.move_id.company_id.currency_id
            balance = line.amount_currency

            if line.move_id.is_special_tc and line.move_id.currency_tc > 0 and\
                line.currency_id and company_currency and line.currency_id != company_currency:

                #_logger.info('\n\nENTRE : _onchange_amount_currency_1\n\n')
                balance = line.currency_id.with_context(default_pen_rate=line.move_id.currency_tc)._convert(
                    line.amount_currency, company.currency_id, company,
                    line.move_id.date or fields.Date.context_today(line))

            elif not line.move_id.is_special_tc and line.currency_id and company_currency and \
                line.currency_id != company_currency:

                date_rate = line.move_id.invoice_date or line.move_id.date or fields.Date.today()

                if line.move_id.move_type in ('in_refund'):
                    date_rate = line.move_id.reversed_entry_id.invoice_date or \
                        line.move_id.reversed_entry_id.date or fields.Date.today()
                elif line.move_id.move_type in ('in_invoice'):
                    date_rate = line.move_id.invoice_date or \
                        line.move_id.date or fields.Date.today()
                else:
                    date_rate = line.move_id.date or fields.Date.today()

                balance = line.currency_id._convert(line.amount_currency, company.currency_id, company, date_rate)

            line.debit = balance if balance > 0.0 else 0.0
            line.credit = -balance if balance < 0.0 else 0.0

            if not line.move_id.is_invoice(include_receipts=True):
                continue
            line.update(line._get_fields_onchange_balance())
            line.update(line._get_price_total_and_subtotal())


    ##########################################################
    @api.model
    def _get_fields_onchange_subtotal(self, price_subtotal=None, move_type=None, currency=None, company=None, date=None):
        self.ensure_one()
        ret=super(AccountMoveLine,self)._get_fields_onchange_subtotal()
        if self.move_id.move_type in ['in_invoice','in_refund'] and self.currency_id != self.company_id.currency_id\
            and not self.move_id.is_special_tc:
            #_logger.info('\n\nGET FIELDS ONCHANGE SUBTOTAL\n\n')
            if self.move_id.move_type in ['in_invoice']:
                #_logger.info('\n\nGET FIELDS ONCHANGE SUBTOTAL RETURN\n\n')
                return self._get_fields_onchange_subtotal_model(
                    price_subtotal=price_subtotal or self.price_subtotal,
                    move_type=move_type or self.move_id.move_type,
                    currency=currency or self.currency_id,
                    company=company or self.move_id.company_id,
                    date=date or self.move_id.invoice_date or self.move_id.date,
                )
            elif self.move_id.move_type in ['in_refund','out_refund']:
                date =self.move_id.reversed_entry_id.invoice_date or \
                            self.move_id.reversed_entry_id.date
                return self._get_fields_onchange_subtotal_model(
                    price_subtotal=price_subtotal or self.price_subtotal,
                    move_type=move_type or self.move_id.move_type,
                    currency=currency or self.currency_id,
                    company=company or self.move_id.company_id,
                    date=date or self.move_id.reversed_entry_id.invoice_date or self.move_id.invoice_date or self.move_id.date,
                )
        
        else:
            return ret

    def _get_fields_onchange_subtotal(self, price_subtotal=None, move_type=None, currency=None, company=None, date=None):
        self.ensure_one()
        #res = super(AccountMoveLine, self)._get_fields_onchange_subtotal(price_subtotal=price_subtotal,move_type=move_type, currency=currency,company=company,date=date)
        if self.move_id.move_type in ['in_refund', 'out_refund']:
            date = self.move_id.reversed_entry_id.invoice_date or \
                            self.move_id.reversed_entry_id.date
        return self._get_fields_onchange_subtotal_model(
            price_subtotal=price_subtotal or self.price_subtotal,
            move_type=move_type or self.move_id.move_type,
            currency=currency or self.currency_id,
            company=company or self.move_id.company_id,
            date=date or self.move_id.date,
        )
