from web3 import Web3
import pandas as pd
import sys; sys.path.insert(0, '..')  # this adds the parent directory into the path, since we want simulations from the parent directory
from camcos.simulations.settings import DATA_PATH

"""
Given a starting and ending block number, this program scrapes block and transaction data and outputs them into a csv
Ensure that you have the web3 library installed. If not, use "pip install web3"
"""

def calldata_gas(hex_string):
    """
    This function calculates the total amount of calldata gas
    :param hex_string: Input string aka calldata
    :return: calldata gas
    """
    hex_string = hex_string[2:] # Remove 0x from the string
    zero_bytes = 0
    non_zero_bytes = 0

    # Iterate through the hexadecimal string, two characters at a time
    for i in range(0, len(hex_string), 2):
        byte = int(hex_string[i:i + 2], 16) # Get the current byte as an integer
        if byte == 0:
            zero_bytes += 1
        else:
            non_zero_bytes += 1
    
    # Returns gas of calldata
    return zero_bytes * 4 + non_zero_bytes * 16

if __name__ == "__main__":
    # Setup RPC endpoint, here we are using a public one from ankr
    web3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))

    # This following block of code checks the date of the block
    # blockNumber = 15627832
    # block = web3.eth.get_block(blockNumber)
    # dt_object = datetime.fromtimestamp(block["timestamp"])
    # print(dt_object)

    block_data = []
    transaction_data = []
    # Set from which block to which block that you'd like to scrape from
    startBlockNum = 15627832
    endBlockNum = 15627932
    # Uncomment the following two lines for Spring 2023 dataset
    # startBlockNum = 16984517
    # endBlockNum = 16984617
    # stepCount gets every nth block from your start to end block number
    stepCount = 1

    for blockNumber in range(startBlockNum, endBlockNum, stepCount):
        block = web3.eth.get_block(blockNumber)
        print(block)

        block_data_single = {
            "blockNumber": blockNumber,
            "gasLimit": block.gasLimit,
            "gasUsed": block.gasUsed,
            "baseFeePerGas": block.baseFeePerGas,
            "difficulty": block.difficulty,
            "hash": block.hash.hex(),
            "transactions": [x.hex() for x in block.transactions]
        }

        block_data.append(block_data_single)

        # Loops through all transactions in the block
        for i in range(len(block.transactions)):
            tx = web3.eth.get_transaction(block.transactions[i])
            calldataGas = calldata_gas(tx.input)
            transaction_data_single = {
                "blockNumber": blockNumber,
                "gas": tx.gas,
                "gasPrice": tx.gasPrice,
                "executionGas": tx.gas - calldataGas,  # Take away calldata gas to get execution gas
                "callDataUsage": calldata_gas(tx.input),
                "callDataLength": len(tx.input),
                "nonce": tx.nonce,
                "to": tx.to,
                "from": tx["from"],
                "calldata": tx.input,
                "transactionID": block.transactions[i].hex()
    }

            transaction_data.append(transaction_data_single)

    # Output files should be under data/. You may rename the files here
    df = pd.DataFrame(block_data)
    df.to_csv(str(DATA_PATH / "blockData.csv"))
    df2 = pd.DataFrame(transaction_data)
    df2.to_csv(str(DATA_PATH / "transactionData.csv"))

