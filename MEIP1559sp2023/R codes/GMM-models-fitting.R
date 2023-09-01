# Read Data Into R 2022 data
tData_2022 <- read.csv("transactionData.csv")
head(tData_2022)

# Read Data Into R 2022 dataset
tData_2023 <- read.csv("transactionData-4-5-2023.csv")
head(tData_2023)

# Combine the two datasets
tData <- rbind(tData_2022,tData_2023[,-8])
head(tData)
dim(tData)

# Split data into two groups
set.seed(9023548)
#Sample for 80% for training(model fitting) and the remaining 20% for test
samp = sample(dim(tData)[1]*.8)
length(samp)  # 24666 training transactions
#raw training data
x=tData[samp,]
dim(x)
#raw test data
test_df <-tData[-samp,]
dim(test_df)

# Plotting the raw execution gas vs call data usage at log scale
library(ggplot2)

p<-ggplot(x, aes(x=log(executionGas), y= log(callDataUsage))) + 
  geom_point() + ggtitle("Ethereum Transactions Datasets") +
  theme(plot.title = element_text(hjust = 0.5)) + labs(x = "Log of Execution Gas",y="Log of Calldata Usage") 
p
#save the figure
#ggsave('tdata2022-2023.png',width = 2, height = 2)


# We remove following last year CAMCOS (this could be improve latter) horizontal lines with more than 1.5% data points from training.
ratiolimit= 0.015
nonvlines_df <- x[intersect(which(x$executionGas %in% sort(unique(tData$executionGas))[table(tData$executionGas) < dim(x)[1]*ratiolimit]),which(x$callDataLength %in% sort(unique(tData$callDataLength))[table(tData$callDataLength) < dim(x)[1]*ratiolimit]) ),]
nonvlines_dfratio = dim(nonvlines_df)[1]/dim(x)[1] # 20.4%. From our exploration section most the vertical lines data points have zero call data.
nonvlines_dfratio



p1<-ggplot(nonvlines_df, aes(x=log(executionGas), y= log(callDataUsage))) + 
  geom_point() + ggtitle("Ethereum Non-Hor. Line Transactions Datasets ") +
  theme(plot.title = element_text(hjust = 0.5)) + labs(x = "Log of Execution Gas",y="Log of Calldata Usage") 

p1


# side by side plot
library(cowplot)
plot_grid(p, p1, labels = "AUTO",scale = c(0.6,0.6))

x['Ttype']<-rep('all',dim(x)[1])
head(x)
nonvlines_df['Ttype'] <-rep('nonhlines',dim(nonvlines_df)[1])
head(nonvlines_df)
df_comb <- rbind(x,nonvlines_df)
head(df_comb)

ggplot(df_comb, aes(x=log(executionGas), y= log(callDataUsage))) + 
  geom_point() +facet_wrap(~Ttype) + ggtitle("Ethereum Transactions Datasets ") +
  theme(plot.title = element_text(hjust = 0.5)) + labs(x = "Log of Execution Gas",y="Log of Calldata Usage") 


# We removed  horizontal lines from test data
nonvlines_df_test <- test_df[intersect(which(test_df$executionGas %in% sort(unique(tData$executionGas))[table(tData$executionGas) < dim(test_df)[1]*ratiolimit]),which(test_df$callDataLength %in% sort(unique(tData$callDataLength))[table(tData$callDataLength) < dim(test_df)[1]*ratiolimit]) ),]
dim(test_df)[1] # 6167
dim(nonvlines_df_test)[1] # 777
nonvlines_df_testratio <-dim(nonvlines_df_test)[1]/dim(test_df)[1]
nonvlines_df_testratio

#Fitting the GMM Model to execution gas and calldata 

library(mixtools)
head(log(nonvlines_df[,c(5,6)]))

# train data
X <- as.matrix(log(nonvlines_df[,c(5,6)]))

# k=2
fit <- mvnormalmixEM(X, lambda = NULL, mu = NULL, sigma = NULL, k = 2,
              arbmean = TRUE, arbvar = TRUE, epsilon = 1e-08,
              maxit = 10000, verb = FALSE)
summary(fit)
# plot 
library(plotGMM)
library(plotmm)
plot_cut_point(fit, plot = TRUE) # returns plot, amerika

#plot components
x<-fit$x
x <- data.frame(x)
ggplot2::ggplot(data.frame(x)) +
  ggplot2::geom_density(ggplot2::aes(x), color="black", fill="black") +
  ggplot2::stat_function(geom = "line", fun = plot_mix_comps,
                         args = list(fit$mu[1], fit$sigma[1], lam = fit$lambda[1]),colour = "red") +
  ggplot2::stat_function(geom = "line", fun = plot_mix_comps,
                         args = list(fit$mu[2], fit$sigma[2], lam = fit$lambda[2]),
                         colour = "blue")

                         


# generate from the fit GMM
library(SBMSplitMerge)
library(mvtnorm)
rmvgmm <- function(n,fit){

# function writing with for loop but can be optimized with vectorization
  g_mat <- matrix(0,n,2)
  for(i in 1:n){
p <- fit$lambda
j <-rcat(1,p)
g_mat[i,]<-as.vector(rmvnorm(1, fit$mu[[j]],sigma =fit$sigma[[j]] ))


  }
  return(g_mat)
}

# Plotting GMM generated vs real data 
comp <-2
g_gmm_df<- rmvgmm(777,fit)
plot(log(nonvlines_df_test$executionGas),log(nonvlines_df_test$callDataUsage), xlab = "log(Execution Gas)", ylab="log(Calldata Usage)", main="Test  Transactions")
points(g_gmm_df,col="red")
legend("bottomright",legend = c("Simulated GMM-2", "Real Data"),col=c("red","black"),pch=1,cex=1)

# Fittiing Multivariate Gaussian (MVG) Model and plotting MVV generated data vs real data

library(mclust)
library(MASS)
fit2<- mvn("XXX",log(nonvlines_df[,c(5,6)]))
simN <- mvrnorm(n=777,as.matrix(fit2$parameters$mean),matrix(fit2$parameters$variance$sigma,2))
plot(log(nonvlines_df_test$executionGas),log(nonvlines_df_test$callDataUsage), xlab = "log(Execution Gas)", ylab="log(Calldata Usage)", main="Test Transactions")
points(simN,col="blue")
points(g_gmm_df,col="red")
legend("bottomright",legend = c("GMM-2 Data","MVG Data", "Real Data"),col=c("red","blue","black"),pch=1,cex=1)
#

comp <- 3
# k=3
fit3 <- mvnormalmixEM(X, lambda = NULL, mu = NULL, sigma = NULL, k = 3,
                     arbmean = TRUE, arbvar = TRUE, epsilon = 1e-08,
                     maxit = 10000, verb = FALSE)
summary(fit3)



#  plotting GMM 3 vs GMM 2 vs real data on training
g_gmm_df3<- rmvgmm(777,fit3)
plot(log(nonvlines_df_test$executionGas),log(nonvlines_df_test$callDataUsage), xlab = "log(Execution Gas)", ylab="log(Calldata Usage)", main="Test Transactions")
points(g_gmm_df3,col="blue")
points(g_gmm_df,col="red")
legend("bottomright",legend = c("GMM-3 Data","GMM-2 Data", "Real Data"),col=c("blue","red","black"),pch=1,cex=1)



#  plotting GMM 3 vs GMM 2 vs real data on training
dim(nonvlines_df[,c(5,6)]) #5035
simN_train <- mvrnorm(n=5035,as.matrix(fit2$parameters$mean),matrix(fit2$parameters$variance$sigma,2))
g_gmm_df3_train <-rmvgmm(5035,fit3)
g_gmm_df_train <-rmvgmm(5035,fit)

# Plotting with ggplot2 on test data
train_df_1 <- nonvlines_df[,c(5,6)]
head(train_df_1)
train_df_1$executionGas<-log(train_df_1$executionGas)
train_df_1$callDataUsage<-log(train_df_1$callDataUsage)
colnames(train_df_1) <-c("LogexecutionGas",  "LogcallDataUsage")
train_df_1['Type']<-rep('Real',dim(nonvlines_df)[1])
head(train_df_1)
#GMM2
train_df_2 <-as.data.frame(g_gmm_df_train)
head(train_df_2)
colnames(train_df_2) <-c("LogexecutionGas",  "LogcallDataUsage")
head(train_df_2)
train_df_2['Type']<-rep('GMM-2',dim(train_df_2)[1])
head(train_df_2)
#GMM3
train_df_3 <-as.data.frame(g_gmm_df3_train)
head(train_df_3)
colnames(train_df_3) <-c("LogexecutionGas",  "LogcallDataUsage")
head(train_df_3)
train_df_3['Type']<-rep('GMM-3',dim(train_df_3)[1])
head(train_df_3)

#Baseline Model
train_df_4 <-as.data.frame(simN_train)
head(train_df_4)
colnames(train_df_4) <-c("LogexecutionGas",  "LogcallDataUsage")
head(train_df_4)
train_df_4['Type']<-rep('MVG',dim(train_df_4)[1])
head(train_df_4)

# combine these test data
df_train<- rbind(train_df_1,train_df_2,train_df_3,train_df_4)
head(df_train)

ggplot(df_train, aes(x=LogexecutionGas, y=LogcallDataUsage,color=Type)) + 
  geom_point()  + ggtitle("Models Fit Comparison on Train Data") +
  theme(plot.title = element_text(hjust = 0.5)) + labs(x = "Log of Execution Gas",y="Log of Calldata Usage")




# Plotting with ggplot2 on test data
test_df_1 <-nonvlines_df_test[,c(5,6)]
head(test_df_1)
test_df_1$executionGas<-log(test_df_1$executionGas)
test_df_1$callDataUsage<-log(test_df_1$callDataUsage)
colnames(test_df_1) <-c("LogexecutionGas",  "LogcallDataUsage")
test_df_1['Type']<-rep('Real',dim(test_df_1)[1])
head(test_df_1)
#GMM2
test_df_2 <-as.data.frame(g_gmm_df)
head(test_df_2)
colnames(test_df_2) <-c("LogexecutionGas",  "LogcallDataUsage")
head(test_df_2)
test_df_2['Type']<-rep('GMM-2',dim(test_df_1)[1])
head(test_df_2)
#GMM3
test_df_3 <-as.data.frame(g_gmm_df3)
head(test_df_3)
colnames(test_df_3) <-c("LogexecutionGas",  "LogcallDataUsage")
head(test_df_3)
test_df_3['Type']<-rep('GMM-3',dim(test_df_1)[1])
head(test_df_3)

#Baseline Model
test_df_4 <-as.data.frame(simN)
head(test_df_4)
colnames(test_df_4) <-c("LogexecutionGas",  "LogcallDataUsage")
head(test_df_4)
test_df_4['Type']<-rep('MVG',dim(test_df_1)[1])
head(test_df_4)

# combine these test data
df_test <- rbind(test_df_1,test_df_2,test_df_3,test_df_4)
head(df_test)

ggplot(df_test, aes(x=LogexecutionGas, y=LogcallDataUsage,color=Type)) + 
  geom_point()  + ggtitle("Models Fit Comparison on Test Data ") +
  theme(plot.title = element_text(hjust = 0.5)) + labs(x = "Log of Execution Gas",y="Log of Calldata Usage")


n=100
library(SBMSplitMerge)
# generate j from the categorical distribution with probability lambda_i, i=1,..,k
p <- fit$lambda
j <-rcat(1,p)
j
# 
#sample from the jth mixture component using a multivariate Gaussian random number generator with mean μj
#and covariance matrix  Sigma_j
library(mvtnorm)
rmvnorm(1, fit$mu[[j]],sigma =fit$sigma[[j]] )

# or calculate manually
# Let A_j be a diagonal matrix containing the eigenvalues of sigma_j
e<-eigen(fit$sigma[[j]])
A_j <-diag(e$values)
A_j
#and V_j be a matrix containing the eigenvectors of C_j along its columns
V_j <- e$vectors
V_j
# Generate a column vector y with entries drawn i.i.d. from the standard normal distribution.
y <- matrix(rnorm(2),ncol = 1)
# Then x = V_jA_j^0.5y_mu_j
V_j%*%(sqrt(A_j)%*%y)+fit$mu[[j]]




fit$lambda[1]*rmvnorm(60, fit$mu[1][1],sigma =fit$sigma[1][1] )+fit$lambda[2]*rmvnorm(60, c(12.348731 , 6.722967),sigma =fit$sigma[2][1])

S_1 <- fit$lambda[[1]]
S_2 <-fit$sigma[[2]]

dmvnormmixt <- function(t,fit){
  S_1 <- fit$sigma[[1]]
  mu_1 <-fit$mu[[1]]
  mu_2 <- fit$mu[[2]]
  S_2 <-fit$sigma[[2]]
  f<-fit$lambda[1]*dmvnorm(t,mean=mu_1,sigma = S_1)+fit$lambda[2]*dmvnorm(t,mean=mu_2,sigma = S_2)
  return(f)
}


install.packages("MCMCpack")
library(MCMCpack)
samples = MCMCmetrop1R(fun=dmvnormmixt
                       , theta.init=1,V=as.matrix(1))

inverse = function (f, lower = -10000, upper = 10000) {
  function (y) uniroot((function (x) f(x) - y), lower = lower, upper = upper)[1]
}

inv_f = inverse(dmvnormmixt, lower=-1.499)

# approximate inversion sampling
N = 200
U = runif(N)
samples = sapply(sapply(U, inv_f),c)




# simulation and EM fits
set.seed(50); 
n=100; x <- rnormmix(n,lbd,mu,sigma)
