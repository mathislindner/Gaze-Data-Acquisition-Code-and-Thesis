import yaml
from yaml.loader import SafeLoader

with open('configuration.yaml') as f:
    config = yaml.load(f, Loader=SafeLoader)
ip_address = config['IP_ADDRESS']
port = config['PORT']

print(ip_address)
print(port)