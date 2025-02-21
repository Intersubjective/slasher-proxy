# dashboard.py
from fastapi import FastAPI
from pony.orm import db_session

from slasher_proxy.common.model import Block, Commitment, NodeStats, Transaction

app = FastAPI(title="Slasher Proxy Dashboard")

@app.get("/dashboard/transactions")
def get_transactions():
    with db_session:
        txs = [t.to_dict() for t in Transaction.select()]
    return {"transactions": txs}

@app.get("/dashboard/commitments")
def get_commitments():
    with db_session:
        commitments = [c.to_dict() for c in Commitment.select()]
    return {"commitments": commitments}

@app.get("/dashboard/blocks")
def get_blocks():
    with db_session:
        blocks = [b.to_dict() for b in Block.select()]
    return {"blocks": blocks}


@app.get("/dashboard/nodestats")
def get_node_stats():
    with db_session:
        stats = [s.to_dict() for s in NodeStats.select()]
    return {"node_stats": stats}
