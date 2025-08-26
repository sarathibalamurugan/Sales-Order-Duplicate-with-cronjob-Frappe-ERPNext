from operator import inv
import frappe
from collections import defaultdict

@frappe.whitelist()
def send_email_cron():
    orders = frappe.get_all(
        "SO Dup",
        filters={"status": "To Bill"},
        fields=["name", "customer_name"]
    )

    # group only order names under each customer
    customer_wise_orders = defaultdict(list)
    for so in orders:
        customer_wise_orders[so.customer_name].append(so.name)
    
    

    for customer, order_names in customer_wise_orders.items():

        
        pdf = []
        try:

            for order_name in order_names:
                inv = frappe.new_doc("Sales Invoice")
                inv.customer = customer
                inv.base_write_off_amount = 0.0
                inv.write_off_amount = 0.0
                inv.base_discount_amount = 0.0
                inv.discount_amount = 0.0
                inv.total = 0.0
                inv.base_total = 0.0
                inv.grand_total = 0.0
                inv.base_grand_total = 0.0
                inv.posting_date = frappe.utils.nowdate()
                inv.due_date = frappe.utils.add_days(inv.posting_date, 30)
                so_doc = frappe.get_doc("SO Dup", order_name)
                for item in so_doc.items:
                    item_code = frappe.db.get_value("Item", {"item_name": item.item_name}, "item_code")
                    if not item_code:
                        print(f"Item code not found for item name: {item.item_name}")
                    inv.append("items", {
                        "item_code": item_code,       # correct field
                        "item_name": item.item_name,
                        "qty": int(item.qty),
                        "rate": float(item.rate),
                        "amount": float(item.amount),
                                                     
                                                     
                                                     
                        "income_account": "Sales - S",
                                
                        })
                inv.debit_to = "Debtors - S"
                inv.company = so_doc.company
                inv.is_opening = "No"    


                for ps in so_doc.payment_schedule:
                    inv.append('payment_schedule', {
                        'due_date': ps.due_date,
                        'invoice_portion': ps.invoice_portion,
                        'payment_amount': ps.payment_amount
                    })


                inv.flags.ignore_mandatory = True        
                inv.save()
                inv.submit()

                inv_mail = frappe.attach_print(
                    inv.doctype,
                    inv.name,
                    print_format="Sales Invoice Print",
                    file_name=f"{inv.name}"
                )
                
                
                
                pdf.append(inv_mail)
                
                

                frappe.db.set_value("SO Dup", order_name, "status", "Completed")
                frappe.db.commit()

        except Exception as e:
            print(e)
        
        frappe.sendmail(
                    recipients=["22csa37@karpagamtech.ac.in"],
                    subject=f"Sales Invoices for {customer}",
                    message=f"Dear {customer},<br><br>Please find attached the sales invoices for your recent orders.<br><br>Best regards,<br>Sarathi",
                    attachments=pdf,
                    now=True,
                )

                 

            
            

       
        
        


            