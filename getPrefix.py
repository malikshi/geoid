import requests
import subprocess
import os
import ipaddress


def get_prefix_cbuijs():
  sourcescbuijs = "https://raw.githubusercontent.com/cbuijs/ipasn/master/country-asia-indonesia.list"
  r = requests.get(sourcescbuijs)
  with open("cbuijs.Indonesia.list", "wb") as IndonesiaIPs:
    IndonesiaIPs.write(r.content)

def get_prefixes_bgp():
    asn_file = "ASN.Indonesia.list"
    output_file = "BGP.Indonesia.list"
    table_url = "https://bgp.tools/table.txt"
    table_file = "table.list"
    backup_table_file = "table-exist.list"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }

    # Rename existing table.txt to table-exist.txt
    if os.path.exists(table_file):
        os.rename(table_file, backup_table_file)
        print(f"Renamed existing {table_file} to {backup_table_file}")

    try:
        # Try downloading table.txt
        print("Downloading table.txt...")
        response = requests.get(table_url, headers=headers)
        response.raise_for_status()

        with open(table_file, "wb") as f:
            f.write(response.content)

        print(f"Download successful. Saved as {table_file}")

        # Remove old table after new download succeed
        os.remove(backup_table_file)

    except requests.exceptions.RequestException as e:
        print(f"Download failed: {e}")
        if os.path.exists(backup_table_file):
            os.rename(backup_table_file, table_file)
            print(f"Reverted to {table_file}")
        else:
            print("No backup table available. Exiting.")
            return

    asns = []
    with open(asn_file, "r") as f:
        for line in f:
            asn = line.split(",")[1].split()[0]  # Extract ASN number
            asns.append(asn)

    with open(output_file, "w") as outfile:
        for asn in asns:
            result = subprocess.run(
                ["grep", "-w", asn, table_file],
                capture_output=True,
                text=True
            )
            outfile.write(result.stdout)
            print("ASN {} processed".format(asn))

    subprocess.run(["sort", "-u", "-o", output_file, output_file])

def filter_prefixes():
    cbuijs_file = "cbuijs.Indonesia.list"
    bgp_file = "BGP.Indonesia.list"
    output_file = "IP.Indonesia.list"

    unique_networks = set()

    for filename in [cbuijs_file, bgp_file]:
      with open(filename, "r") as f:
          for line in f:
              try:
                  prefix = line.split()[0]  # Extract prefix from BGP list if needed
                  if filename == bgp_file:
                      # Remove the trailing ASN from BGP.Indonesia.list line
                      prefix = prefix.split()[0]
                  # Handle both IPv4 and IPv6 prefixes
                  if ":" in prefix:
                      network = ipaddress.ip_network(prefix.strip(), strict=False)  # Allow mixed notation for IPv6
                  else:
                      network = ipaddress.ip_network(prefix.strip())
                  unique_networks.add(network)
              except ValueError:
                  print(f"Invalid IP address/prefix in {filename}: {line}")

    # Custom Sorting Function (IPv4 first, then IPv6)
    def sort_key(network):
        return (network.version == 6, network)  # Sort by version (IPv4=4, IPv6=6), then by network address

    # Write unique prefixes to IP.Indonesia.list
    with open(output_file, "w") as f:
        for network in sorted(unique_networks, key=sort_key):
            f.write(f"{network}\n")

if __name__ == "__main__":
    get_prefix_cbuijs()
    get_prefixes_bgp()
    filter_prefixes()
