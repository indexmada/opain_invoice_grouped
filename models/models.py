# -*- coding: utf-8 -*-

from odoo import models, fields, api

class resPartner(models.Model):
	_inherit = "res.partner"

	group_invoice = fields.Boolean("Facture Groupée")

class PosOrder(models.Model):
	_inherit="pos.order"

	invoice_count = fields.Integer("Nombre de Facture", default=1)
	invoice_group_id = fields.Many2one(string="Facture Groupée", comodel_name="account.invoice")

	@api.multi
	def get_grouped_invoice(self):
		context = self._context.copy()
		invoice_ids = self.invoice_group_id
		return {
			'type': 'ir.actions.act_window',
			'name': 'Facture groupée',
			'res_model': 'account.invoice',
			'views': [(self.env.ref('account.invoice_tree_with_onboarding').id, 'tree'),
						(self.env.ref('account.invoice_form').id, 'form')],
			'context': context,
			'domain': [('id', 'in', invoice_ids.mapped('id'))],
			'target': 'current',
		}

class AccountInvoice(models.Model):
	_inherit="account.invoice"

	pos_order_grouped_ids = fields.Many2many(string="Commandes groupées", comodel_name="pos.order")

class PosSession(models.Model):
	_inherit = 'pos.session'

	pos_order_grouped_ids = fields.Many2many(string="Orders group", comodel_name="pos.order")

	def _on_close_pos_session(self):
		orders = self.order_ids
		invoice_obj = self.env['account.invoice'].sudo()
		invoice_line_obj = self.env['account.invoice.line'].sudo()

		print('_'*100)
		print(orders)
		partner_obj = self.env['res.partner'].sudo()		
		for customer in orders.mapped('partner_id'):
			print(customer, ' ', partner_obj, ' ', customer.group_invoice)
			if (customer not in partner_obj) and (customer.group_invoice == True):
				partner_obj |= customer
				invoice_vals = {
						'type': 'out_invoice',
						'partner_id': customer.id,

				}
				new_invoice = invoice_obj.sudo().create(invoice_vals)
				print(new_invoice)

				customer_orders = orders.filtered(lambda order: order.partner_id == customer)
				print(customer_orders)

				# POS Order line
				# invoice_line_tab = []
				for order_line in customer_orders.mapped('lines'):
					invoice_line_vals = {
						'product_id': order_line.product_id.id,
						'name': order_line.product_id.display_name,
						'quantity': order_line.qty,
						'price_unit': order_line.price_unit,
						'price_subtotal': order_line.price_subtotal_incl,
						# 'sale_line_ids': order_line,
						'uom_id': order_line.product_id.uom_id.id,
						'invoice_id': new_invoice.id,
						'account_id': new_invoice.account_id.id
					}
					order_line.order_id.write({'invoice_group_id': new_invoice.id})
					print(invoice_line_vals)
					new_line = invoice_line_obj.create(invoice_line_vals)
					for tax in order_line.tax_ids_after_fiscal_position:
						new_line.write({'invoice_line_tax_ids': [(4,tax.id)]})
					if order_line.order_id not in new_invoice.pos_order_grouped_ids:
						new_invoice.write({'pos_order_grouped_ids': [(4, order_line.order_id.id)]})

				new_invoice.action_invoice_open()