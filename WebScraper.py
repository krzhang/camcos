import csv, requests, cloudscraper, time
from bs4 import BeautifulSoup as bs
from collections import deque
times = []



# This code is very hacky and still in "testing mode", so please mind the unreadability. 

def extractData(txn_hash):
    url = "https://etherscan.io/tx/" + str(txn_hash)
    scraper = cloudscraper.create_scraper()
    # start = time.time()
    page = scraper.get(url)
    
    # set up BS object
    soup = bs(page.content, 'html.parser')
    gp = soup.find(id='ContentPlaceHolder1_spanGasPrice')
    gl = soup.find(id='ContentPlaceHolder1_spanGasLimit')
    tf = soup.find(id='ContentPlaceHolder1_spanTxFee')
    ts = soup.find(id='clock')
    pt = soup.find(class_='fal fa-stopwatch ml-1')

    if gp is None or gl is None or tf is None:
        return txn_hash, "fail"

    # get gas price and only take the first element (omitting units like "ether")
    gp = gp.get_text().split()[0]
    # get gas limit
    gl = gl.get_text().replace(',', '');
    # get transaction fee, omitting units again
    tf = tf.get_text().split()[0]
    # get timestamp
    ts = ts.next_sibling.next_sibling.split('(')[1][:-1]
    # get pending time
    if (pt != None):
        pt = ''.join(pt.next_sibling.split()[2:])
    
    data_lst = ",".join([str(gp), str(gl), str(tf), str(ts), str(pt)])

    return data_lst, "pass"


if __name__ == '__main__':
    failed_txn = deque()
    out_data = deque()
    txns = 0
    
    #loop through all txns a first time, adding all failed txns to our deque
    with open('Transactions10_01_2020.csv') as data:
        parser = csv.reader(data)
        next(parser)
        print("First Loop:")
        for row in parser:
            begin = time.time()
            dt_lst, status = extractData(row[0])
            end = time.time()
            if status == "fail":
                failed_txn.append(row[0])

                #print summary data to terminal
                print("average time per tx: ", round(sum(times) / len(times), 2), " seconds  ",
                " total succesful txns:  ", txns, "  failed txns: ", len(failed_txn), "  percent failed: ", 
                round((len(failed_txn)/(txns + len(failed_txn))) * 100, 2), end = '\r')
                continue
            dt_lst = dt_lst + "," + row[0] + "\n"
            out_data.append(dt_lst)
            txns += 1

            # print summary data to terminal
            times.append(end-begin)
            print("average time per tx: ", round(sum(times) / len(times), 2), " seconds  ",
                " total succesful txns:  ", txns, "  failed txns: ", len(failed_txn), "  percent failed: ", 
                round((len(failed_txn)/(txns + len(failed_txn))) * 100, 2), end = '\r')
    
    #pop txns off the failed deque and try them again. keep doing this until failed_txn is empty
    if(failed_txn):
        print("Failed Txns:")
    while failed_txn:
        txn = failed_txn.popleft()
        txn_data, status = extractData(txn)
        if status == "fail":
            failed_txn.append(txn_data)
            continue
        txn_data = txn_data + "," + txn + "\n"
        out.data.append(txn_data)

        txns += 1

    print("Data scraped. Writing to file...")
    
    with open("../../time_data.csv", "w") as f:
        f.write("gasPrice," + "gasLimit," + "txFee," + "timestamp," + "pendingTime," + "txnHash\n")
        for item in out_data:
            f.write(item)

