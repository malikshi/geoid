import os
import ipaddress
import json

DATA_DIR = "data_out"
RELEASE_DIR = "release_out"

os.makedirs(RELEASE_DIR, exist_ok=True)

def build_lists():
    cbuijs_file = os.path.join(DATA_DIR, "cbuijs.Indonesia.list")
    bgp_file = os.path.join(DATA_DIR, "BGP.Indonesia.list")
    ipinfo_file = os.path.join(DATA_DIR, "ipinfo.Indonesia.list")
    
    unique_networks = set()
    
    files_to_check = [cbuijs_file, bgp_file, ipinfo_file]
    
    for filename in files_to_check:
        if not os.path.exists(filename):
            continue
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    prefix = line.split()[0]
                    
                    if ":" in prefix:
                        network = ipaddress.ip_network(prefix, strict=False)
                    else:
                        network = ipaddress.ip_network(prefix)
                    unique_networks.add(network)
                except ValueError:
                    pass

    # Sort networks
    def sort_key(network):
        return (network.version == 6, network)
        
    sorted_networks = sorted(unique_networks, key=sort_key)
    
    # Generate formats
    
    # 1. Plain Text
    with open(os.path.join(RELEASE_DIR, "IP.Indonesia.list"), "w") as f:
        for net in sorted_networks:
            f.write(f"{net}\n")
            
    # 2. Nginx allowed config
    with open(os.path.join(RELEASE_DIR, "nginx-allow.conf"), "w") as f:
        for net in sorted_networks:
            f.write(f"allow {net};\n")
            
    # 3. Nginx deny config
    with open(os.path.join(RELEASE_DIR, "nginx-deny.conf"), "w") as f:
        for net in sorted_networks:
            f.write(f"deny {net};\n")

    # 4. Sing-box Rule Set JSON Format
    # Loyalsoldier/geoip format is SRS. We export a json for it to compile:
    rule_set = {
        "version": 1,
        "rules": [
            {
                "ip_cidr": [str(net) for net in sorted_networks]
            }
        ]
    }
    
    with open(os.path.join(RELEASE_DIR, "indonesia.json"), "w") as f:
        json.dump(rule_set, f, indent=2)

if __name__ == "__main__":
    build_lists()
