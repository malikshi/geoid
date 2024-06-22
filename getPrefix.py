import requests
import subprocess
import os

sourcescbuijs = "https://raw.githubusercontent.com/cbuijs/ipasn/master/country-asia-indonesia.list"

r = requests.get(sourcescbuijs)
with open("IP.Indonesia.list", "wb") as IndonesiaIPs:
  IndonesiaIPs.write(r.content)

def get_prefixes():
    asn_file = "ASN.Indonesia.list"
    output_file = "BGP.Indonesia.list"
    table_url = "https://bgp.tools/table.txt"
    table_file = "table.txt"
    backup_table_file = "table-exist.txt"

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
            

if __name__ == "__main__":
    get_prefixes()
