from datetime import datetime
import pandas as pd
import requests
import time
import json
import csv
import sys

import MySQLdb


class FBM(object):
	def __init__(self, url):
		self.url = url
		self.session = requests.Session()
		self._grocery_list = None

		database_info = None

		with open('database_info.json') as f:
			database_info = json.load(f)

		self.db = MySQLdb.connect(**database_info)
		self.cur = self.db.cursor()

	@property
	def grocery_list(self):
		if self._grocery_list is None:
			self.cur.execute("SELECT * FROM grocery_list")
			self._grocery_list = self.cur.fetchall()
			self._grocery_list = tuple(i[0] for i in self._grocery_list)
		return self._grocery_list


	def auth(self, user, password):
		payload = {
			'username': user,
			'password': password,
			'location': '1',
			'action': 'Login'
		}
		self.session.post('https://' + self.url + '/login/', data=payload)

	def GetDonors(self):
		try:
			return self.donor_table
		except AttributeError:
			payload = {
				'fileName': "",
				'col[donors.donors_79fe2d07e8]': '1',
				'col[donors.firstName]': '1',
				'col[donors.middleName]': '1',
				'col[donors.lastName]': '1',
				'col[donors.donors_e0feeaff84]': '1',
				'col[donors.donors_730b308554]': '1',
				'col[donors.donors_b4d4452788]': '1',
				'col[donors.streetAddress]': '1',
				'col[donors.city]': '1',
				'col[donors.zipCode]': '1',
				'col[donors.donors_6213775871]': '1',
				'col[donations.donationTypeSum]': '1',
				'conditions[type]': 'And',
				'conditions[1][field]': 'donors.created_at',
				'conditions[1][action]': 'dlte',
				'conditions[1][value]': time.strftime('%Y-%m-%d'),
				'conditions[1][id]': '1',
				'conditions[1][blockType]': 'item',
				'conditions[1][parent]': "",
				'blockCount': '2'
			}
			r = self.session.post('https://' + self.url +
							'/reports/donor/donors/csv/',
							data=payload,
							stream=True)
			r.raw.decode_content = True
			self.donor_table = csv.reader(str(r.raw.data).split('\n'))
		return self.donor_table

	def GetDonations(self):
		try:
			return self.donation_table
		except AttributeError:
			payload = {
				'fileName': '',
				'donation_type': '0',
				'col[donors.id]': '1',
				'col[donors.firstName]': '1',
				'col[donors.middleName]': '1',
				'col[donors.lastName]': '1',
				'col[donors.donors_e0feeaff84]': '1',
				'col[donors.donors_b4d4452788]': '1',
				'col[donors.city]': '1',
				'col[donors.state]': '1',
				'col[donors.zipCode]': '1',
				'col[donors.created_at]': '1',
				'col[donors.donors_6213775871]': '1',
				'col[donations.donationType_id]': '1',
				'col[donations.donations_1b458b4e6a]': '1',
				'col[donations.donation_at]': '1',
				'col[donations.donations_41420c6893]': '1',
				'col[donations.donations_f695e975c6]': '1',
				'conditions[type]': 'And',
				'conditions[1][field]': 'donations.donation_at',
				'conditions[1][action]': 'dlte',
				'conditions[1][value]': time.strftime('%Y-%m-%d'),
				'conditions[1][id]': '1',
				'conditions[1][blockType]': 'item',
				'conditions[1][parent]': '',
				'blockCount': '2'
			}
			r = self.session.post('https://' + self.url +
							'/reports/donor/donations/csv/',
							data=payload,
							stream=True)
			r.raw.decode_content = True
			self.donation_table = csv.reader(str(r.raw.data).split('\n'))
		return self.donation_table

	def AddDonationToTable(self, df):
		for i, row in df.iterrows():
			query = """INSERT INTO `food_donor_data` (
			`Donation ID`, 
			`Zip/Postal Code`, 
			`Weight (lbs)`, 
			`Company / Organization Name`, 
			`Memo`, 
			`State/Province`, 
			`Donation Type`, 
			`Quantity Type`, 
			`Source of Donation`, 
			`Donor Type`, 
			`Street Address`, 
			`City/Town`, 
			`Value (approximate $)`, 
			`First Name`, 
			`Apartment`, 
			`Spouse Name (First, Last)`, 
			`Salutation Greeting (Dear So and So)`, 
			`Donated On`, 
			`Last Name`, 
			`Donor ID`, 
			`Quantity`, 
			`Middle Name`, 
			`Email Address`, 
			`Name of Food Item`, 
			`Food Item Category`, 
			`DonorCategory`
			) VALUES 
			(
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s) ON DUPLICATE KEY UPDATE;"""

			try:
				self.cur.execute(query, tuple(row[i] for i in ["Donation ID","Zip/Postal Code","Weight (lbs)","Company / Organization Name","Memo","State/Province","Donation Type","Quantity Type","Source of Donation","Donor Type","Street Address","City/Town","Value (approximate $)","First Name","Apartment","Spouse Name (First, Last)","Salutation Greeting (Dear So and So)","Donated On","Last Name","Donor ID","Quantity","Middle Name","Email Address","Name of Food Item","Food Item Category","DonorCategory"]))
			except:
				print self.cur._last_executed
				raise
			self.db.commit()

	def FindDonationType(self, df):
		df["DonorCategory"] = ""
		for i, row in df.iterrows():
			don_type = None
			data_dict = row.to_dict()
			# Waste
			if don_type is None:
				if "Food" in data_dict["First Name"] and "Waste" in data_dict["Last Name"]:
					don_type = "Waste"
			# Purchased food
			if don_type is None:
				if "Food Bank" in data_dict["First Name"] and "Purchased food" in data_dict["Last Name"]:
					don_type = "Purchased"
			# TEFAP
			if don_type is None:
				if "TEFAP" in data_dict["First Name"]:
					don_type = "TEFAP"
			# Anonymous (classified as individual)
			if don_type is None:
				if "Anonymous" in data_dict["First Name"]:
					don_type = "Individual"
			# Senior Boxes (this must cone before Church)
			if don_type is None:
				if "Senior Boxes" in data_dict["Name of Food Item"]:
					don_type = "Senior program"
			# Grocery
			if don_type is None:
				for store in self.grocery_list:
					if data_dict["First Name"].lower().startswith(store.lower()):
						don_type = "Grocery"
			# Church
			if don_type is None:
				for type in ["church", "st."]:
					if type in data_dict["First Name"].lower() or type in data_dict["Company / Organization Name"].lower():
						don_type = "Church"
			# Individual
			if don_type is None:
				if len(data_dict["Company / Organization Name"]) == 0 and len(data_dict["First Name"]) < 20 and len(data_dict["Last Name"]) < 20:
					don_type = "Individual"
			# Other Org/Corp
			if don_type is None:
				don_type = "Org/Corp"

			df.at[i, "DonorCategory"] = don_type
		return df
		
	def GetFoodDonations(self, start, end):
		"""
		Gets food donations (report Food Donations)
		
		:param datetime start: Start date
		:param datetime end: End date
		:return dict: Dist table return
		"""

		payload = {	
			'donation_type': '1',
			'col[donors.id]': '1',
			'col[donors.donors_79fe2d07e8]': '1',
			'col[donors.firstName]': '1',
			'col[donors.middleName]': '1',
			'col[donors.lastName]': '1',
			'col[donors.donors_e0feeaff84]': '1',
			'col[donors.donors_c42c9d40e7]': '1',
			'col[donors.donors_b4d4452788]': '1',
			'col[donors.streetAddress]': '1',
			'col[donors.apartment]': '1',
			'col[donors.city]': '1',
			'col[donors.state]': '1',
			'col[donors.zipCode]': '1',
			'col[donors.donorType_id]': '1',
			'col[donations.donationType_id]': '1',
			'col[donations.donations_1b458b4e6a]': '1',
			'col[donations.donation_at]': '1',
			'col[donations.donations_1704817e34]': '1',
			'col[donations.donations_0968598e1b]': '1',
			'col[donations.donations_b09ad16128]': '1',
			'col[donations.donations_6af401c28c]': '1',
			'col[donations.donations_f695e975c6]': '1',
			'col[donations.donations_e0a1fae0a3]': '1',
			'col[donations.donations_6058571536]': '1',
			'conditions[type]': 'And',
			'conditions[1][field]': 'donations.donation_at',
			'conditions[1][action]': 'dgte',
			'conditions[1][value]': start.strftime('%Y-%m-%d'), # start date
			'conditions[1][id]': '1',
			'conditions[1][blockType]': 'item',
			'conditions[2][field]': 'donations.donation_at',
			'conditions[2][action]': 'dlte',
			'conditions[2][value]': end.strftime('%Y-%m-%d'), # end date
			'conditions[2][id]': '2',
			'conditions[2][blockType]': 'item',
			'blockCount': '3'
		}
		r = self.session.post('https://' + self.url +
						'/reports/donor/donations/csv/',
						data=payload,
						stream=True)
		r.raw.decode_content = True
		donation_table = list(csv.reader(str(r.raw.data).split('\n')))
		headers = donation_table.pop(0)
		donation_table = pd.DataFrame.from_records(donation_table[:-1], columns=headers)
		donation_table = self.FindDonationType(donation_table)
		return donation_table

		
	def PostDonation(self, D_id, dollars, pounds, D_type, date):
		donation_type = [
			"",
			"Individual Donor",
			"Churches/Places of Worship",
			"Grants/Foundations",
			"Business/Corporation/Organization",
			"Fundraising Events",
			"Board of Directors",
			"Recurring Monthly Donation",
			"NTFH Event",
			"Other Revenue"
		]

		payload = {
		'action': 'Save Donation & close',
		'donationType_id': '1',
		'donation_at': date,
		'donations_1b458b4e6a': donation_type[int(D_type)],
		'donations_e0a1fae0a3': dollars,
		'donations_f695e975c6': pounds
		}

		r = self.session.post('https://' + self.url +
						'/create-new-donation/create/did:' + str(D_id) + '/',
						data=payload)
		return r.status_code

	def AddDonor(self, donor_json):
		params = json.loads(donor_json)
		payload = {
			'donors_1f13985a81': 'N/A',
			'firstName': params['first'],
			'lastName': params['last'],
			'donors_e0feeaff84': params['email'],
			'donors_730b308554': 'N/A',
			'streetAddress': params['street'],
			'city': params['town'],
			'state': params['state'],
			'zipCode': params['zip'],
			'donorType_id': '1',
			'action': 'Save'
		}
		r = self.session.post('https://' + self.url +
						'/create-new-donation/donor/create/',
						data=payload)
		return r.status_code
		

if __name__ == '__main__':
	pd.set_option('display.expand_frame_repr', False)

	if len(sys.argv) < 4:
		print "Usage: 'task' 'user' 'pass' etc..."
		exit(1)
	q = FBM("mcfb.soxbox.co")
	q.auth(sys.argv[2], sys.argv[3])
	if sys.argv[1] == "donors":
		donor_list = q.GetDonors()
		headers = next(donor_list)
		for row in donor_list:
			print "{"
			for a, b in zip(row, headers):
				print "\"" + b + "\": \"" + a + "\","
			print "},"
	elif sys.argv[1] == "add_donor":
		# json formatted input wih the following params
		# first, last, email, street, tow, state, zip
		print q.AddDonor(sys.argv[4])
	elif sys.argv[1] == "add_donation":
		# type user pass donor_id pounds donation_type date (YYYY-MM-DD)
		print q.PostDonation(sys.argv[4], 0, sys.argv[5], sys.argv[6], sys.argv[7])
	elif sys.argv[1] == "fooddonations":
		# start-date, end-date (format mm-dd-yyyy
		start = datetime.strptime(sys.argv[4], "%m-%d-%Y")
		end = datetime.strptime(sys.argv[5], "%m-%d-%Y")
		donor_list = q.GetFoodDonations(start, end)
		donor_list.to_csv("out.csv", sep=',')
		print donor_list
