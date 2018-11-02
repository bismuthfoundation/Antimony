#!/usr/bin/env python3
"""
Console mode basic wallet - Connects to Wallet server, console mode.
No need for a local node, but needs a wallet.der in the current dir.

EggdraSyl - Nov. 2018.

Thanks to @icook

# TODO: add -wallet option
# TODO: support encrypted wallets
# TODO: log to file?

# TODO: create wallet if not exists.
"""

import base64
import click
import json
import logging
# import pprint
import re
import requests
import sys
import time

from Cryptodome.Hash import SHA
from Cryptodome.PublicKey import RSA
from Cryptodome.Signature import PKCS1_v1_5

from modules import rpcconnections


__version__ = '0.0.31'


VERBOSE = False


def check_address(address):
    if not re.match('[abcdef0123456789]{56}', address):
        app_log.error("{} is not a valid address".format(address))
        sys.exit()


def keys_load(keyfile="wallet.der"):
    # import keys
    try:
        with open (keyfile, 'r') as keyfile:
            wallet_dict = json.load (keyfile)
        private_key_readable = wallet_dict['Private Key']
        public_key_readable = wallet_dict['Public Key']
        address = wallet_dict['Address']
        try:  # unencrypted
            key = RSA.importKey(private_key_readable)
            encrypted = False
            unlocked = True
        except:  # encrypted
            encrypted = True
            unlocked = False
            key = None
        if (len(public_key_readable)) != 271 and (len(public_key_readable)) != 799:
            raise ValueError("Invalid public key length: {}".format(len(public_key_readable)))
        public_key_hashed = base64.b64encode(public_key_readable.encode('utf-8'))
        return key, public_key_readable, private_key_readable, encrypted, unlocked, public_key_hashed, address, keyfile
    except Exception as e:
        app_log.error("Error {} loading {}".format(e, keyfile))
        sys.exit()


def get_active_servers_list():
    try:
        rep = requests.get("http://api.bismuth.live/servers/wallet/legacy.json")
        if rep.status_code == 200:
            wallets = rep.json()
            # We have a server list, order by load
            sorted_wallets = sorted([wallet for wallet in wallets if wallet['active']],
                                    key=lambda k: (k['clients'] + 1) / (k['total_slots'] + 2))
            return sorted_wallets
    except Exception as e:
        app_log.error("Error {} getting Server list from API.".format(e))


def connect(ctx):
    """Tries to connect to a server, depending on the context. Fetches from API if needed."""
    if ctx.obj.get('connection', None):
        return
    if ctx.obj['host'] != 'auto':
        try:
            connection = rpcconnections.Connection((ctx.obj['host'], ctx.obj['port']), verbose=ctx.obj['verbose'])
            ctx.obj['connection'] = connection
        except Exception as e:
            app_log.error("Error {} connecting to {}:{}.".format(e, ctx.obj['host'], ctx.obj['port']))
            sys.exit()
        return
    else:
        # Auto mode
        servers = get_active_servers_list()
        for server in servers:
            try:
                connection = rpcconnections.Connection((server['ip'], server['port']), verbose=ctx.obj['verbose'])
                ctx.obj['connection'] = connection
                # First ok is the one
                return
            except Exception as e:
                app_log.warning("Error {} connecting to {}:{}.".format(e, server['ip'], server['port']))
        # No active server or all failed
        app_log.error("Error, no available server.")
        sys.exit()


def load_keys(ctx, address=''):
    """Load local keys unless an address is given. If address, then returns."""
    if ctx.obj.get('key', None):
        return
    if address:
        ctx.obj['key'] = None
        ctx.obj['address'] = address
        ctx.obj['privkey'] = None
        ctx.obj['pubkey'] = None
        return
    # Or load from wallet.der
    key, public_key_readable, private_key_readable, encrypted, unlocked, public_key_hashed, address, keyfile = \
        keys_load("wallet.der")
    if encrypted:
        app_log.error("Encrypted wallet, unsupported yet.")
        sys.exit()
    ctx.obj['key'] = key
    ctx.obj['address'] = address
    ctx.obj['privkey'] = private_key_readable
    ctx.obj['pubkey'] = public_key_readable


@click.group()
@click.option('--host', '-h', default="auto", help='Force bismuth server host (default=auto)')
@click.option('--port', '-p', default=8150, help='Bismuth server port')
@click.option('--verbose', '-v', default=False)
@click.pass_context
def cli(ctx, port, host, verbose):
    global VERBOSE
    ctx.obj['host'] = host
    ctx.obj['port'] = port
    ctx.obj['verbose'] = verbose
    VERBOSE = verbose
    ctx.obj['connection'] = None


@cli.command()
@click.pass_context
def servers(ctx):
    """List all active wallet servers"""
    servers = get_active_servers_list()
    for server in servers:
        print("{}:{} \t {}".format(server['ip'], server['port'], server['label']))


@cli.command()
@click.pass_context
def version(ctx):
    """Print version"""
    print("Antimony version {}".format(__version__))


@cli.command()
@click.pass_context
@click.argument('address', default='', type=str)
def balance(ctx, address):
    """Get balance of an ADDRESS (Uses the one from local wallet.der by default)"""
    connect(ctx)
    load_keys(ctx, address)
    if VERBOSE:
        print("Connected to {}".format(ctx.obj['connection'].ipport))
        print("address {}".format(ctx.obj['address']))
    con = ctx.obj['connection']
    balance = con.command('balanceget', [ctx.obj['address']])
    balance.insert(0, ctx.obj['address'])
    keys = ["address", "balance", "total_credits", "total_debits", "total_fees", "total_rewards", "balance_no_mempool"]
    balance = dict(zip(keys, balance))
    print(json.dumps(balance))
    return balance


@cli.command()
@click.pass_context
@click.argument('recipient', type=str)
@click.argument('amount', default=0, type=float)
@click.argument('data', default='', type=str)
@click.argument('operation', default='', type=str)
@click.argument('above', default=0, type=float)
def send(ctx, recipient, amount, data='', operation='', above=0):
    """Send Bis or data to a RECIPIENT. DATA is an optional message.
    OPERATION is optional and should be empty for regular transactions.
    ABOVE is optional, if > 0 then the tx will only be sent when balance > ABOVE"""

    check_address(recipient)
    load_keys(ctx)
    connect(ctx)
    con = ctx.obj['connection']

    if above > 0:
        my_balance = float(con.command('balanceget', [ctx.obj['address']])[0])
        if my_balance <= above:
            if VERBOSE:
                app_log.warning("Balance too low, {} instead of required {}, dropping.".format(my_balance, above))
            print(json.dumps({"result": "Error", "reason": "Balance too low, {} instead of required {}"
                             .format(my_balance, above)}))
            return

    myaddress = ctx.obj['address']
    public_key_hashed = base64.b64encode(ctx.obj['pubkey'].encode('utf-8'))

    tx_timestamp = '%.2f' % time.time()
    transaction = (tx_timestamp, myaddress, recipient, '%.8f' % float(amount), operation, data)  # this is signed, float kept for compatibility

    h = SHA.new(str(transaction).encode("utf-8"))
    signer = PKCS1_v1_5.new(ctx.obj['key'])
    signature = signer.sign(h)
    signature_enc = base64.b64encode(signature)
    txid = str(signature_enc.decode("utf-8"))[:56]
    if VERBOSE:
        app_log.info("Client: Encoded Signature: {}".format(signature_enc.decode("utf-8")))

    verifier = PKCS1_v1_5.new(ctx.obj['key'])

    if verifier.verify(h, signature):
        if VERBOSE:
            app_log.info("Client: The signature is valid, proceeding to save transaction")
        tx_submit = (tx_timestamp, myaddress, recipient, '%.8f' % float(amount), str(signature_enc.decode("utf-8")),
                     str(public_key_hashed.decode("utf-8")), operation, data)

        reply = con.command('mpinsert', [tx_submit])
        if VERBOSE:
            app_log.info("Server replied '{}'".format(reply))
        if not reply:
            reply = "Server timeout"
        if reply[-1] == "Success":
            if VERBOSE:
                app_log.info("Transaction accepted to mempool")
            print(json.dumps({"result": "Success", "txid": txid}))
        else:
            # app_log.error("Error: {}".format(reply))
            print(json.dumps({"result": "Error", "reason": reply}))
    else:
        app_log.error("Invalid signature")


if __name__ == '__main__':
    logger = logging.getLogger('push')

    app_log = logging.getLogger()
    app_log.setLevel(logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(levelname)-5s] %(message)s')
    ch.setFormatter(formatter)
    app_log.addHandler(ch)

    cli(obj={})

