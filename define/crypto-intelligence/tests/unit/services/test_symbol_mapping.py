import json

# Load symbol mapping
with open('crypto-intelligence/data/symbol_mapping.json', 'r') as f:
    mapping = json.load(f)

# Test addresses
test_addr = '0x562e36288a9dd867d5d8b0aa48c2e8d2d215d5d'
mapping_addr = '0x562e362876c8aee4744fc2c6aac8394c312d215d'

print(f"Test address:    {test_addr}")
print(f"Mapping address: {mapping_addr}")
print(f"Match: {test_addr == mapping_addr}")
print()

# Check if test address is in mapping
if test_addr in mapping:
    print(f"Test address FOUND in mapping:")
    print(json.dumps(mapping[test_addr], indent=2))
else:
    print(f"Test address NOT FOUND in mapping")

print()

# Check if mapping address is in mapping
if mapping_addr in mapping:
    print(f"Mapping address FOUND in mapping:")
    print(json.dumps(mapping[mapping_addr], indent=2))
else:
    print(f"Mapping address NOT FOUND in mapping")
