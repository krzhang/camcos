# Split data into two groups
set.seed(9023548)
samp = sample(dim(tData)[1]*.8)
x=tData[samp,]
ratiolimit= 0.015
other <- x[intersect(which(x$executionGas %in% sort(unique(tData$executionGas))[table(tData$executionGas) < dim(x)[1]*ratiolimit]),which(x$callDataLength %in% sort(unique(tData$callDataLength))[table(tData$callDataLength) < dim(x)[1]*ratiolimit]) ),]
otherratio = dim(other)[1]/dim(x)[1]
plot(log(x$executionGas),log(x$callDataLength), xlab = "log(GasValue)", ylab="log(Calldata Length)", main="Ethereum Transactions with Line Clusters")
plot(log(other$executionGas),log(other$callDataLength), xlab = "log(GasValue)", ylab="log(Calldata Length)", main="Ethereum Transactions without Line Clusters")

library(ContaminatedMixt)
library(MASS)
fit <- CNmixt(log(other[,c(5,7)]),1,model="VVV",contamination=TRUE)
plot(fit,xlab = "log(GasValue)", ylab="log(Calldata Length)", main="Contaminated Normal")
summary(fit)
simCN <- rCN(n=1000*.759,c(12.4472,6.8918),matrix(c(.37586,.012123,.012123,0.78518),2),0.75903,5.2437)
plot(log(other$executionGas),log(other$callDataLength), xlab = "log(GasValue)", ylab="log(Calldata Length)", main="Ethereum Transactions without Line Clusters")
points(simCN,col="red")
legend("bottomright",legend = c("Simulated Contaminated Normal Data", "Real Data"),col=c("red","black"),pch=1,cex=1)

library(mclust)
fit2<- mvn("XXX",log(other[,c(5,7)]))
simN <- mvrnorm(n=1000*.759,as.matrix(fit2$parameters$mean),matrix(fit2$parameters$variance$sigma,2))
plot(log(other$executionGas),log(other$callDataLength), xlab = "log(GasValue)", ylab="log(Calldata Length)", main="Ethereum Transactions without Line Clusters")
points(simN,col="blue")
legend("bottomright",legend = c("Simulated Normal Data", "Real Data"),col=c("blue","black"),pch=1,cex=1)

# Testing
testx = tData[-samp,c(5,7)]
n = dim(testx)[1]
plot(log(testx$executionGas),log(testx$callDataLength), xlab = "log(GasValue)", ylab="log(Calldata Length)", main="Test Data")
simCN <- mvrnorm(n=n*otherratio,as.matrix(fit2$parameters$mean),matrix(fit2$parameters$variance$sigma,2))
points(simCN,col="red")

#1 dimensional data
dim1 = unique(x[-which(x$executionGas %in% sort(unique(tData$executionGas))[table(tData$executionGas) < dim(x)[1]*ratiolimit]),5])
ratios = rep(0,length(dim1))
for (i in 1:length(dim1)){
  tofit <- x[x$executionGas == dim1[i],7]
  ratios[i] <- length(tofit)/length(x$executionGas == dim1[i])
  m <- round(n*ratios[i]*(1-otherratio))
  if (max(table(tofit))/sum(table(tofit)) > 0.5){
    points(rep(log(dim1[i]),m),rep(log(max(table(tofit))),m),col="green")  
  }else{
    fitgam <- fitdistr(tofit, densfun = "gamma")
    points(rep(log(dim1[i]),m),log(rgamma(m,fitgam$estimate[1],fitgam$estimate[2])),col="green")  
  }
}


dim1 = unique(x[-which(x$callDataLength %in% sort(unique(tData$callDataLength))[table(tData$callDataLength) < dim(x)[1]*ratiolimit]),7])
ratios = rep(0,length(dim1))
for (i in 1:length(dim1)){
  tofit <- x[x$callDataLength == dim1[i],5]
  ratios[i] <- length(tofit)/length(x$callDataLength == dim1[i])
  m <- round(n*ratios[i]*(1-otherratio))
  if (max(table(tofit))/sum(table(tofit)) > 0.5){
    points(rep(log(max(table(tofit))),m),rep(log(dim1[i]),m),col="green")  
  }else{
    fitgam <- fitdistr(tofit, densfun = "gamma",start = list(shape = 1, rate = 1),lower=c(0.1,0.1))
    points(log(rgamma(m,fitgam$estimate[1],fitgam$estimate[2])),rep(log(dim1[i]),m),col="green")  
  }
}

