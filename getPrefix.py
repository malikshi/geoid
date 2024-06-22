import requests



sourcescbuijs = "https://raw.githubusercontent.com/cbuijs/ipasn/master/country-asia-indonesia.list"
sourcesbgptools = "https://bgp.tools/table.txt"

r = requests.get(sourcescbuijs)
with open("IP.Indonesia.list", "wb") as IndonesiaIPs:
  IndonesiaIPs.write(r.content)