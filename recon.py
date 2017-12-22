import pprint
import requests
from collections import defaultdict

pp = pprint.PrettyPrinter(indent=2)

req = requests.get('http://127.0.0.1:13413/v1/chain')
tip = req.json()
bhash = tip['hash']

def get_block(bhash):
	req = requests.get('http://127.0.0.1:13413/v1/blocks/' + bhash)
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

count = 0
while count < 1000:
	block = get_block(bhash)
	print(block)
	for x in block['inputs']:
		inputs[x['commit']].append(x)
	for x in block['outputs']:
		outputs[x['commit']].append(x)
	bhash = block['previous']
	count += 1

for x in inputs.values():
	if len(x) > 1:
		print('**** duplicate input: ' + x)

for x in outputs.values():
	if len(x) > 1:
		print('**** duplicate output: ' + x)


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

print('# inputs: ' + str(len(inputs)))
print('# output: ' + str(len(outputs)))
print('# unspent outputs: ' + str(unspent_count))
