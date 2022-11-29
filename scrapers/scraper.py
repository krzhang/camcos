from web3 import Web3, EthereumTesterProvider
import pandas as pd

if __name__ == "__main__":
    web3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))


    # df = pd.read_csv("blockData.csv")
    # df2 = pd.read_csv("transactionData.csv")

    s = 0

    block_data = []
    transaction_data = []
    # 15817058
    for blockNumber in range(15627832, 15627932, 1):
        block = web3.eth.get_block(blockNumber)
        print(block)
        # df.loc[blockNumber + 1] = [
        #     blockNumber,
        #     block.gasLimit,
        #     block.gasUsed,
        #     block.baseFeePerGas,
        #     block.difficulty,
        #     block.hash.hex(),
        #     [x.hex() for x in block.transactions]
        # ]
        # df.to_csv("blockData.csv", index=False)

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

        for i in range(len(block.transactions)):
            tx = web3.eth.get_transaction(block.transactions[i])

            # df2.loc[s] = [
            #     blockNumber,
            #     tx.gas,
            #     tx.gasPrice,
            #     tx.input,
            #     len(tx.input),
            #     tx.nonce,
            #     tx.to,
            #     tx["from"]
            # ]
            # df2.to_csv("transactionData.csv", index=False)
            # s+=1

            transaction_data_single = {
                "blockNumber":blockNumber,
                "gas":tx.gas,
                "gasPrice":tx.gasPrice,
                "input":tx.input,
                "callDataUsage":len(tx.input),
                "nonce": tx.nonce,
                "to":tx.to,
                "from":tx["from"]
            }
            transaction_data.append(transaction_data_single)

    df = pd.DataFrame(block_data)
    df.to_csv("blockDataContinuous.csv")
    df2 = pd.DataFrame(transaction_data)
    df2.to_csv("transactionDataContinuous.csv")
