bData <- read.csv(file.choose())
tData <- read.csv(file.choose())
reg <- lm(gasPrice ~ gas + callDataUsage, data=tData)
summary(reg)
plot(log(tData$executionGas),log(tData$callDataUsage))

# Finding where the calldata and gas "lines" are
commonCall <- sort(table(tData$callDataUsage),decreasing=TRUE)
commonGas <- sort(table(tData$executionGas),decreasing=TRUE)


unique(tData[tData$callDataUsage == 0,]$blockNumber) # There are many different blocks that have 0 calldata

# Checking common gass values
tData[tData$executionGas == names(commonGas)[1],]
unique(tData[tData$executionGas == names(commonGas)[1],]$blockNumber) # similar for common gas


# Trying to find the diagonal lines
plot(log(tData$executionGas-tData$callDataLength-tData$callDataUsage),log(tData$callDataUsage))
# No luck yet