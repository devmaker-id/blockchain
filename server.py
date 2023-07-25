import sys
import hashlib
import json
import random

from time import time
from uuid import uuid4

from flask import Flask
from flask.globals import request
from flask.json import jsonify

import requests
from urllib.parse import urlparse


class Blockchain(object):
    difficulty_target = "0000"

    def hash_block(self, block):
        block_encoded = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha512(block_encoded).hexdigest()

    def __init__(self):
        self.nodes = set()
        self.devnet = []
        self.chain = []
        self.wallet = []

        self.current_transactions = []

        genesis_hash = self.hash_block(000000000)

        self.append_block(
            hash_of_previous_block=genesis_hash,
            nonce=self.proof_of_work(0, genesis_hash, [])
        )

    def add_node(self, address):
        parse_url = urlparse(address)
        self.nodes.add(parse_url.netloc)
        print(parse_url.netloc)

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            if block['hash_of_previous_block'] != self.hash_block(last_block):
                return False

            if not self.valid_proof(
                    current_index,
                    block['hash_of_previous_block'],
                    block['transaction'],
                    block['nonce']):
                return False

            last_block = block
            current_index += 1

        return True

    def update_blockchain(self):
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            response = requests.get(f'http://{node}/api/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

                if new_chain:
                    self.chain = new_chain
                    return True

        return False

    def proof_of_work(self, index, hash_of_previous_block, transactions):
        nonce = 0

        while self.valid_proof(index, hash_of_previous_block, transactions, nonce) is False:
            nonce += 1

        if transactions:
            self.valid_transaction(transactions)

        return nonce

    def valid_transaction(self, transactions):
        index_trx = 0
        while index_trx < len(transactions):
            trx_data = transactions[index_trx]

            sender_trx = self.find_wallet(trx_data['sender'])
            if not self.update_balance_address(
                sender_trx['address'],
                trx_data['balance_send'],
                plus=False,
                minus=True
            ):
                return ('update balance pengirim gagal!')

            recipient_trx = self.find_wallet(trx_data['recipient'])
            if not self.update_balance_address(
                recipient_trx['address'],
                trx_data['balance_send'],
                plus=True,
                minus=False
            ):
                return ('update balance penerima gagal!')

            index_trx += 1

        return True

    def valid_proof(self, index, hash_of_previous_block, transactions, nonce):
        content = f'{index}{hash_of_previous_block}{transactions}{nonce}'.encode()

        content_hash = hashlib.sha256(content).hexdigest()

        return content_hash[:len(self.difficulty_target)] == self.difficulty_target

    def append_block(self, nonce, hash_of_previous_block):
        block = {
            'index': len(self.chain),
            'time': int(time()),
            'transaction': self.current_transactions,
            'nonce': nonce,
            'hash_of_previous_block': hash_of_previous_block
        }

        self.current_transactions = []

        self.chain.append(block)
        return block

    def add_transaction(self, parse, sender, recipient, balance_send):
        sender_data = self.find_wallet(sender, hash=True)
        recipient_data = self.find_wallet(recipient)

        if not sender_data:
            return ('address pengirim tidak terdaftar', 401)

        if not recipient_data:
            return ('address penerima tidal terdaftar', 401)

        hash_verify = self.hash_verify(sender_data['address'], parse)
        if sender_data['hash'] != hash_verify:
            return ('parse tidak sesuai bos')
        if sender_data['balance'] <= balance_send:
            return ('balance coint tidak cukup bos!')

        self.current_transactions.append({
            'balance_send': balance_send,
            'recipient': recipient_data['address'],
            'sender': sender_data['address'],
            'time': int(time())
        })
        respons = self.last_block['index'] + 1

        return ('BLOCK : ', respons)

    def hash_verify(self, wallet, seed):
        return hashlib.sha512(wallet.encode() + seed.encode()).hexdigest()

    def all_wallet(self):
        gen_wallet = []

        with open('src/wallet/wallet.json', 'r') as wFs:
            obj_wallet = json.load(wFs)

            for address in obj_wallet['data']:
                gen_wallet.append({
                    "address": address['address'],
                    "balance": address['balance']
                })

        return gen_wallet

    def add_wallet(self):
        new_wallet = str(uuid4()).replace('-', "")
        with open('src/config/salt.json', 'r') as fs:
            fa = json.load(fs)
            seed = " ".join(random.choices(fa, k=12))
            nWallet = "".join(["98xQ", new_wallet])

            wallet = {
                'address': nWallet,
                'balance': 0,
                'parse': seed,
                'verify_hash': blockchain.hash_verify(nWallet, seed),
                'time': int(time())
            }

        with open('src/wallet/wallet.json', 'r+') as file:
            file_data = json.load(file)
            file_data['data'].append(wallet)
            file.seek(0)
            json.dump(file_data, file, indent=4)

        # blockchain.wallet.append(wallet)
        return {
            'message': 'save you parse, required',
            'address': nWallet,
            'parse': seed,
            'balance': 0,
        }

    def find_wallet(self, address, hash=False):
        count_wallet = []

        with open('src/wallet/wallet.json', 'r') as files:
            objWallet = json.load(files)

        for wlt in objWallet['data']:
            if wlt['address'] == address:
                if hash:
                    count_wallet = {
                        'hash': wlt['hash'],
                        'balance': wlt['balance'],
                        'address': wlt['address']
                    }
                else:
                    count_wallet = {
                        'balance': wlt['balance'],
                        'address': wlt['address']
                    }

        return count_wallet

    def update_balance_address(self, address, req_balance, plus=False, minus=False):
        for wallet in self.wallet:
            if wallet['address'] == address:
                if plus:
                    wallet['balance'] = wallet['balance'] + req_balance
                elif minus:
                    wallet['balance'] = wallet['balance'] - req_balance
        return True

    @property
    def last_block(self):
        return self.chain[-1]


app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', "")

blockchain = Blockchain()
# route coin


@app.route('/', methods=['GET'])
def coin():
    with open('src/config/devnet.json', 'r') as files:
        fs = json.load(files)

    return jsonify(fs), 200

# route wallet


@app.route('/api/wallet', methods=['GET'])
def wallet():
    address = blockchain.all_wallet()

    return jsonify(address), 200


@app.route('/api/wallet/<address>', methods=['GET'])
def get_wallet(address):

    if not blockchain.all_wallet():
        return jsonify({
            'message': 'nothing wallet is blockchain'
        }), 403

    count_address = blockchain.find_wallet(address)

    if not count_address:
        return jsonify({
            'message': 'wallet cant be registerd'
        }), 404

    return jsonify({
        'amount': count_address['balance'],
        'wallet': count_address['address']
    }), 200


@app.route('/api/wallet/new', methods=['GET'])
def create_wallet():
    response = blockchain.add_wallet()

    return jsonify(response), 200

# routes


@app.route('/api/chain', methods=['GET'])
def full_chain():
    response = blockchain.chain

    return jsonify(response), 200


@app.route('/api/miner', methods=['POST'])
def mine_block():
    values = request.get_json()

    if not values['address']:
        return ('Value address Not found', 400)

    count_miner_wallet = blockchain.find_wallet(values['address'])

    if not count_miner_wallet:
        response = {
            'status': 'failed',
            'data': {
                'wallet': values['wallet'],
                'info': 'wallet not registred'
            }
        }
        return (jsonify(response), 200)

    blockchain.add_transaction(
        parse="remember weather earth occur swung cap west citizen clean seat throughout refused",
        sender="98xQ000000000000000000000000000000",
        recipient=count_miner_wallet['address'],
        balance_send=100
    )

    last_block_hash = blockchain.hash_block(blockchain.last_block)

    index = len(blockchain.chain)
    nonce = blockchain.proof_of_work(
        index, last_block_hash, blockchain.current_transactions)

    block = blockchain.append_block(nonce, last_block_hash)
    response = {
        'status': "success",
        'index': block['index'],
        'hash_of_previous_block': block['hash_of_previous_block'],
        'nonce': block['nonce'],
        'transaction': block['transaction']
    }
    return (jsonify(response), 200)


@app.route('/api/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required_fields = ['parse', 'sender', 'recipient', 'amount']
    if not all(k in values for k in required_fields):
        return ('Missing fields', 400)
    last_transactions = blockchain.add_transaction(
        values['parse'],
        values['sender'],
        values['recipient'],
        values['amount']
    )

    print(last_transactions)
    response = {
        'status': 'success',
        'data': f'Pending Block {last_transactions}'
    }
    return (jsonify(response), 201)


@app.route('/api/transactions', methods=['GET'])
def get_trx():
    values = request.get_json()
    address = values.get('address')
    paramsType = values.get('type_params')

    trx_last = []
    for trx in blockchain.chain:

        if trx['transaction'] is None:
            trx_last = []

        for res_trx in trx['transaction']:
            trx_last.append({
                "hash": trx['hash_of_previous_block'],
                "block": trx['nonce'],
                "time": res_trx['time'],
                "value": res_trx['balance_send'],
                "sender": res_trx['sender'],
                "recipient": res_trx['recipient']
            })

        params = []
        if paramsType:
            if paramsType == "sender":
                for fetch in trx_last:
                    if address == fetch['sender']:
                        params.append(fetch)
            elif paramsType == "recipient":
                for fetch in trx_last:
                    if address == fetch['recipient']:
                        params.append(fetch)
        else:
            params = trx_last

    return jsonify(params), 200


@app.route('/api/nodes/add_nodes', methods=['POST'])
def add_nodes():
    values = request.get_json()
    nodes = values.get('nodes')

    if nodes is None:
        return "Error, missing node(s) info", 400

    for node in nodes:
        blockchain.add_node(node)

    response = {
        'message': 'Node baru telah di tambahkan',
        'nodes': list(blockchain.nodes)
    }

    return jsonify(response), 200


@app.route('/api/nodes/sync', methods=['GET'])
def sync():
    updated = blockchain.update_blockchain()
    if updated:
        response = {
            'message': 'Blockchain telah diupdtae dengan data terbaru',
            'blockchain': blockchain.chain
        }
    else:
        response = {
            'message': 'Blockchain sudah menggunakan data paling baru',
            'blockchain': blockchain.chain
        }

    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='1510')
