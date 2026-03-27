import os
import gzip
import json
import requests
from lxml import etree
import subprocess

DATA_DIR = "data_out"
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_bgp_asn():
    print("Fetching ASN.Indonesia.list...")
    url = "https://bgp.he.net/country/ID"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    tree = etree.HTML(r.text)
    
    with open(os.path.join(DATA_DIR, "ASN.Indonesia.list"), "w") as f:
        for asn_row in tree.xpath('//*[@id="asns"]/tbody/tr'):
            asn_number = asn_row.xpath('td[1]/a/text()')[0].replace('AS', '')
            asn_name = asn_row.xpath('string(td[2])').strip()
            f.write(f"IP-ASN,{asn_number} // {asn_name}\n")

def fetch_cbuijs():
    print("Fetching cbuijs.Indonesia.list...")
    url = "https://raw.githubusercontent.com/cbuijs/ipasn/master/country-asia-indonesia.list"
    r = requests.get(url)
    r.raise_for_status()
    with open(os.path.join(DATA_DIR, "cbuijs.Indonesia.list"), "wb") as f:
        f.write(r.content)

def fetch_bgp_table():
    print("Fetching bgp table.txt...")
    url = "https://bgp.tools/table.txt"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    with open(os.path.join(DATA_DIR, "table.txt"), "wb") as f:
        f.write(r.content)
        
    print("Extracting BGP.Indonesia.list from table.txt...")
    asns = []
    with open(os.path.join(DATA_DIR, "ASN.Indonesia.list"), "r") as f:
        for line in f:
            asn = line.split(",")[1].split()[0]
            asns.append(asn)
            
    table_file = os.path.join(DATA_DIR, "table.txt")
    bgp_out = os.path.join(DATA_DIR, "BGP.Indonesia.list")
    
    with open(bgp_out, "w") as outfile:
        # Optimization: use grep to grab all ASNs efficiently
        for asn in asns:
            result = subprocess.run(
                ["grep", "-w", asn, table_file],
                capture_output=True,
                text=True
            )
            outfile.write(result.stdout)
    
    subprocess.run(["sort", "-u", "-o", bgp_out, bgp_out])

def fetch_ipinfo():
    print("Fetching ipinfo data...")
    token = os.environ.get("IPINFO_TOKEN")
    if not token:
        print("Warning: IPINFO_TOKEN not set, skipping IPinfo data.")
        return
        
    url = f"https://ipinfo.io/data/free/country_asn.json.gz?token={token}"
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        print(f"Failed to fetch IPinfo data. Status: {r.status_code}")
        return
        
    # Read ASNs from ASN.Indonesia.list
    indonesia_asns = set()
    try:
        with open(os.path.join(DATA_DIR, "ASN.Indonesia.list"), "r") as f:
            for line in f:
                parts = line.split(",")
                if len(parts) > 1:
                    asn = parts[1].split()[0]
                    indonesia_asns.add(asn)
    except FileNotFoundError:
        print("ASN.Indonesia.list not found. Cannot filter IPinfo by ASN.")
        return
        
    out_file = os.path.join(DATA_DIR, "ipinfo.Indonesia.list")
    
    import ipaddress
    from collections import defaultdict
    data_map = defaultdict(lambda: {'ipv4': set(), 'ipv6': set()})
    
    print("Parsing ipinfo database stream...")
    with gzip.GzipFile(fileobj=r.raw) as gz:
        for line_bytes in gz:
            try:
                line = line_bytes.decode('utf-8')
                entry = json.loads(line)
                asn_raw = entry.get('asn', '')
                
                if asn_raw:
                    asn = asn_raw.upper().replace('AS', '')
                    if asn in indonesia_asns:
                        network_str = entry.get('network', entry.get('route', ''))
                        
                        # Handle start_ip/end_ip fallback
                        if not network_str and 'start_ip' in entry and 'end_ip' in entry:
                            start = ipaddress.ip_address(entry['start_ip'])
                            end = ipaddress.ip_address(entry['end_ip'])
                            cidrs = ipaddress.summarize_address_range(start, end)
                            for cidr in cidrs:
                                if cidr.version == 4:
                                    data_map[asn]['ipv4'].add(cidr)
                                else:
                                    data_map[asn]['ipv6'].add(cidr)
                            continue
                            
                        if network_str:
                            try:
                                network = ipaddress.ip_network(network_str, strict=False)
                                if network.version == 4:
                                    data_map[asn]['ipv4'].add(network)
                                else:
                                    data_map[asn]['ipv6'].add(network)
                            except ValueError:
                                continue
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            except Exception:
                pass
                
    print(f"Database loaded. Found entries for {len(data_map)} valid Indonesian ASNs.")
    
    with open(out_file, "w") as f:
        # Sort and write all networks
        all_networks = set()
        for asn_data in data_map.values():
            all_networks.update(asn_data['ipv4'])
            all_networks.update(asn_data['ipv6'])
            
        # Write sorted networks
        for net in sorted(all_networks, key=lambda n: (n.version == 6, n)):
            f.write(str(net) + "\n")

if __name__ == "__main__":
    fetch_bgp_asn()
    fetch_cbuijs()
    fetch_bgp_table()
    fetch_ipinfo()
