# Copyright (c) 2025, parthasarathi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SODup(Document):
	

	def before_save(self):

		self.company = "Sarathi"
		if self.customer_name:
			customer = frappe.db.get_value(
				"Customer", self.customer_name, "customer_name"
			)
			if customer:
				self.customer_name = customer
				frappe.msgprint("Customer already exists: " + customer)
			else:
				new_customer = frappe.new_doc("Customer")
				new_customer.customer_name = self.customer_name
				new_customer.customer_type = "Individual"
				
				new_customer.save()
				self.customer_name = new_customer.customer_name
				self.customer = new_customer.name
				frappe.msgprint("New Customer Created: " + new_customer.name)
		else:
			frappe.throw("Customer is required to create Sales Order")

			
		if not self.date:
			self.date = frappe.utils.nowdate()
			frappe.msgprint("Today Date Added")
		
		if not self.delivery_date:
			frappe.throw("Delivery Date is required to create Sales Order")

		if not self.payment_schedule:
			self.append('payment_schedule', {
				
				'due_date': self.delivery_date,
				'invoice_portion': 100,
				'payment_amount': self.total
			})
			



		total = 0
		total_qty = 0	
		if self.items:
			
			for item in self.items:
				exist = frappe.db.get_value(
					"Item", item.item_name, "item_name"
				)


				item.delivery_date = self.delivery_date

				print(exist)
				print(item.item_name)
				

				if not exist:
					new_item = frappe.new_doc("Item")
					new_item.item_name = item.item_name
					new_item.item_code = item.item_name
					new_item.item_group = "Products"
					new_item.stock_uom = "Nos"
					new_item.is_stock_item = 1
					new_item.save()
					exist = new_item
					frappe.msgprint("New Item Created")

				else:
					
					frappe.msgprint("Item already exists: " + item.item_name)
				
				if item.qty <= 0:
					item.qty = 1
				
				exist_price = frappe.db.sql(
					'''SELECT price_list_rate FROM `tabItem Price` WHERE item_name = %s''',
					(item.item_name,), as_dict=True
				)

				if not exist_price:
					item.rate = item.rate
					new_price = frappe.new_doc("Item Price")
					new_price.item_name = item.item_name
					new_price.item_code = exist.item_code
					new_price.uom = "Nos"
					new_price.currency = "INR"
					new_price.price_list = "Standard Selling"
					new_price.price_list_rate = item.rate
					new_price.save()

					

				else:
					item.rate = exist_price[0].price_list_rate
					
				
				total += int(item.qty) * int(item.rate)
				item.amount = int(item.qty) * int(item.rate)
				total_qty += int(item.qty)
				

		
		else:
			frappe.throw("Items are required to create Sales Order")

		self.grand_total = total
		self.total_quantity = total_qty
		self.total = total
		self.status = "Draft"

		

	def on_submit(self):
		frappe.db.set_value("SO Dup",self.name,"status","To Bill")
		frappe.db.commit()
		frappe.msgprint("Sales Order Submitted and is To Bill")
		
