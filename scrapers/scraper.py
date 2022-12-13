from web3 import Web3, EthereumTesterProvider
import pandas as pd

if __name__ == "__main__":
    # Setup RPC endpoint, here we are using a public one from ankr
    web3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))

    block_data = []
    transaction_data = []
    startBlockNum = 15627832
    endBlockNum = 15627932
    stepCount = 1

    for blockNumber in range(startBlockNum, endBlockNum, stepCount):
        block = web3.eth.get_block(blockNumber)
        print(block)

        block_data_single = {
            "blockNumber":blockNumber,
            "gasLimit":block.gasLimit,
            "gasUsed": block.gasUsed,
            "baseFeePerGas":block.baseFeePerGas,
            "difficulty":block.difficulty,
            "hash":block.hash.hex(),
            "transactions":[x.hex() for x in block.transactions]
        }
        block_data.append(block_data_single)

        # Loops through all transactions in the block
        for i in range(len(block.transactions)):
            tx = web3.eth.get_transaction(block.transactions[i])
            input_string = tx.input
            if len(input_string)>10000:
                input_string = ""
            transaction_data_single = {
                "blockNumber":blockNumber,
                "gas":tx.gas,
                "gasPrice":tx.gasPrice,
                "input":input_string,
                "callDataUsage":len(input_string),
                "nonce": tx.nonce,
                "to":tx.to,
                "from":tx["from"]
            }
            transaction_data.append(transaction_data_single)

    df = pd.DataFrame(block_data)
    df.to_csv("blockDataContinuous.csv")
    df2 = pd.DataFrame(transaction_data)
    df2.to_csv("transactionDataContinuous.csv")
