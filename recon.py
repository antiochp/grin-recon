import pprint
import requests
from collections import defaultdict

pp = pprint.PrettyPrinter(indent=2)

req = requests.get('http://127.0.0.1:13413/v1/chain')
tip = req.json()
bhash = tip['hash']

print('Current chain head: %s at %s' % (tip['hash'], tip['height']))
print('Looking back through blocks...\n')
def get_utxo(hash):
	req = requests.get('http://127.0.0.1:13413/v1/chain/utxos/byids?id=' + hash)
	utxo = req.json()
	# fix this (pull batches at a time)
	if utxo:
		return {
			'commit': utxo[0]['commit'],
			'height': utxo[0]['height'],
		}

def get_utxos_at_height(height):
	url = 'http://127.0.0.1:13413/v1/chain/utxos/atheight?start_height=%s&end_height=%s' % (height, height)
	print(url)
	req = requests.get(url)
	utxos = req.json()
	pp.pprint(utxos)

def get_block(hash):
	req = requests.get('http://127.0.0.1:13413/v1/blocks/' + hash)
	block = req.json()

	inputs = []
	for x in block['inputs']:
		inputs.append({
			'commit': x,
			'height': block['header']['height'],
		})

	outputs = []
	for x in block['outputs']:
		outputs.append({
			'output_type': x['output_type'],
			'commit': x['commit'],
			'height': block['header']['height'],
		})

	return {
		'height': block['header']['height'],
		'hash': block['header']['hash'],
		'previous': block['header']['previous'],
		'inputs': inputs,
		'outputs': outputs,
	}

inputs = defaultdict(list)
outputs = defaultdict(list)
utxos = defaultdict(list)

current = tip['height']
while current > 0:
	block = get_block(bhash)

	for x in block['inputs']:
		inputs[x['commit']].append(x)
	for x in block['outputs']:
		outputs[x['commit']].append(x)
	bhash = block['previous']
	current -= 1
	if current % 250 == 0:
		print('...slowly making progress...', current)

duplicate_inputs = []
for x in inputs.values():
	if len(x) > 1:
		duplicate_inputs.append(x)
		print('**** Found duplicate input: ')
		pp.pprint(x)

duplicate_outputs = []
for x in outputs.values():
	if len(x) > 1:
		duplicate_outputs.append(x)
		print('**** Found duplicate output: ')
		pp.pprint(x)

print('... getting all the utxos ...')
for x in outputs.keys():
	utxo = get_utxo(x)
	if utxo:
		utxos[x].append(utxo)

print('\n')
print('# Inputs:', len(inputs))
print('# Outputs:', len(outputs))
print('# Duplicate Inputs:', len(duplicate_inputs))
print('# Duplicate Outputs:', len(duplicate_outputs))

for x in inputs.keys():
	input = inputs.get(x)[0]
	output = outputs.get(x)
	if output:
		output = output[0]
		output['height_spent'] = input['height']

unspent_count = 0
for x in outputs.values():
	if not x[0].get('height_spent'):
		unspent_count += 1

print('# Unspent outputs: ' + str(unspent_count))
print('\n')
print('Now checking for discrepencies with the current UTXO set (please be patient) ...')

spent_but_utxo = 0
unspent_no_utxo = 0

print('Spent outputs still in UTXO set')
print('-------------------------------')
for output in outputs.values():
	output = output[0]
	utxo = utxos.get(output['commit'])
	if output.get('height_spent') and utxo:
		spent_but_utxo += 1
		pp.pprint(output)
		pp.pprint(utxo)
print('\n')

print('Unspent outputs missing from the UTXO set')
print('-----------------------------------------')
for output in outputs.values():
	output = output[0]
	utxo = utxos.get(output['commit'])
	if not output.get('height_spent') and not utxo:
		unspent_no_utxo += 1
		pp.pprint(output)
		pp.pprint(utxo)
print('\n')

print('--------------------')
print('Inputs: ', len(inputs))
print('Outputs: ', len(outputs))
print('*** Duplicate (sets) of inputs: ', len(duplicate_inputs))
print('*** Duplicate (sets) of outputs: ', len(duplicate_outputs))
print('*** Spent yet still in UTXO set: ', spent_but_utxo)
print('*** Unspent but missing from UTXO set: ', unspent_no_utxo)
print('--------------------')
