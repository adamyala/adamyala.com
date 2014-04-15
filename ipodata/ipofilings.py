from bs4 import BeautifulSoup, NavigableString
from datetime import date
import requests
import re
import csv

# Accepts a string and a list of html tags
# Returns the string with the open and close parts of the listed tags removed
def replace_multi_tag(replace_string, replace_list):
	for item in replace_list:
		replace_string = replace_string.replace(item, "")
		replace_string = replace_string.replace(item[0] + "/" + item[1:], "")
	return replace_string

# Accepts a string, and a start and an end substring as parameters
# Returns a string of the substrings and characters between them
def start_end_string(source, start, end):
	a = str(source).find(start)
	b = str(source).find(end) + len(end)
	return str(source)[a:b]

# The below two defs were taken from http://docs.python.org/2/library/csv.html
# BeautifulSoup doesn't seem to play well with csv
def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
	# csv.py doesn't do Unicode; encode temporarily as UTF-8:
	csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
							dialect=dialect, **kwargs)
	for row in csv_reader:
		# decode UTF-8 back to Unicode, cell by cell:
		yield [unicode(cell, 'utf-8') for cell in row]
def utf_8_encoder(unicode_csv_data):
	for line in unicode_csv_data:
		yield line.encode('utf-8')

# Load the filings webpage and pass it through BeautifulSoup
listpage = requests.get("http://www.nasdaq.com/markets/ipos/activity.aspx?tab=filings").content
html = BeautifulSoup(listpage)

# Grab all links to each company's page
htmllinks = html.findAll('a', attrs={'href': re.compile("http://www.nasdaq.com/markets/ipos/company")})

# Clear current contents of the csv file
wt = open("ipo.csv",'w+')
wt.close()

# Create the csv file we'll be writing to
with open("ipo.csv",'wb') as resultfile:
	wr = csv.writer(resultfile, dialect='excel')

	# Adds the date and a blank row
	wr.writerow([date.today(),"NASDAQ - IPOs"])
	wr.writerow(["",""])

	# Iterate through all the links
	for link in htmllinks:

		# Find the start and end of the web address substring
		# then open that webpage
		# print start_end_string(link, "http", ">")[:-2]
		tablepage = BeautifulSoup(requests.get(start_end_string(link, 'http', '" ')[:-2]).content)

		# Get the table containing the company data we want
		tablerows = tablepage.findAll("div", { "id" : "infoTable" } )[0].findAll("td")

		# Iterate through those rows. We only need the first 10 elements
		# The step is set to two because information is put into the 
		# csv in two "columns"
		for x in range(0,10,2):
			if x == 6:
				# The 6th element is the company site and label
				# We find the start and end of the web address, then remove the tags
				# The elements are written the csv as a row
				wr.writerow([replace_multi_tag(str(tablerows[x]), ["<td>","<br/>"]),start_end_string(str(tablerows[x+1]), "http", "com")])
			else:
				# The elements are written the csv as a row
				wr.writerow([replace_multi_tag(str(tablerows[x]), ["<td>","<br/>"]),replace_multi_tag(str(tablerows[x+1]), ["<td>","<br/>"])])

		# Part one of the company description is found via class
		# The start and end are identified, then trimmed out
		descrp1 = tablepage.find("div", { "class" : "ipo-comp-description" })
		descrp1 = replace_multi_tag(start_end_string(descrp1, "<pre>", "</pre>"),["<pre>"])

		# Part two of the company description
		descrp2 = tablepage.find("div", { "id" : "read_more_div_toggle1" })
		descrp2 = replace_multi_tag(start_end_string(descrp2, "<pre>", "</pre>"),["<pre"])

		# Descriptions are written to the csv
		wr.writerow(["Company Description", descrp1+descrp2])

		# A blank row is added between company info blocks
		wr.writerow(["",""])
