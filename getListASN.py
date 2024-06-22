import requests
from lxml import etree

def save_latest_asns():
    url = "https://bgp.he.net/country/ID" 
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    r = requests.get(url=url, headers=headers)
    r.raise_for_status()

    tree = etree.HTML(r.text)

    with open("ASN.Indonesia.list", "w") as asn_file:
        for asn_row in tree.xpath('//*[@id="asns"]/tbody/tr'):
            asn_number = asn_row.xpath('td[1]/a/text()')[0].replace('AS', '')
            asn_name = asn_row.xpath('string(td[2])').strip()

            asn_info = f"IP-ASN,{asn_number} // {asn_name}"
            asn_file.write(asn_info + "\n") # Output every ASN without filtering


if __name__ == "__main__":
    save_latest_asns()