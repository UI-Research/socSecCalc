# This program calculates the estimates monthly social security retirement
# benefit for primary earner retirees. The first goal is to set-up the
# basic, no-work set-up.

# First load package dependencies. Pandas should be sufficient for now
import pandas as pd

# First read in the csv file with year maximum earnings and indexing factor
ssParam = pd.read_csv("calculationParam.csv", header = 0)
avgWages = pd.read_csv("awi.csv", header = 0)

ssParam.index = ssParam["Year"]
ssParam = ssParam.drop("Year", axis = 1)

avgWages.index = avgWages["year"]
avgWages = avgWages.drop("year", axis = 1)

# Create a function to calculate average earnings
# In this intitial iteration, it will expect either a full list of earnings
# or a single year of earnings and a growth factor. The user will also need to
# provide an age at retirement and the year of retirement. At the moment
# the earliest year we have max earnings and indexing for are 1956, so the
# years of earnings can only go back to 1956. Will assume work starting at
# age 18.

# Year - year of retirement
# Age - age at retirement
# Earnings - Either earnings at year prior to retirement or a stream of wages
#            assumed to go end with the year of retirement. A future version
#            might expand this to a dictionary where we allow values in
#            the stream to be tied to specific years.
# singleEarn - A flag indicating whether earnings is for the final year
#              or a stream. True is for a single year, false is for a stream.
# grate - The growth rate of the wages relative to the national average.

def calcSS(year, age, earnings, singleEarn = True, grate = 0.02,
           ssparm = ssParam, avgWages = avgWages):
     # If they put in a single year, we have to go backwords to age 18
     if singleEarn == True:
        earnings = calcStream(year, age, earnings, grate, avgWages) 
        

# calcStream is a helper function that projects wages backwards
# for a given person with reported earnings for a single year
# and a given wage. This obviously will smooth out wage changes,
# so we might want to consider a different method of obtaining
# estimated wages. This is currently set up to match the basic
# social security calculator. 
def calcStream(year, age, earnings, grate, myWages):

    # drop years outside ages 18-current age
    myWages = myWages.loc[(year-(age-18)):year,]

    # set up the wage column and put earnings for that year in the
    # correct row for that column
    myWages.loc[year, "wage"] = earnings
    
    # loop through to put correct wages in the dataframe
    for i in range(year-1,year-(age-18)-1, -1):
        wageNY = myWages.loc[i+1, "wage"]
        changeTY = myWages.loc[i, "change"]
        myWages.loc[i, "wage"] = wageNY/((1+grate)*changeTY)

    return myWages.drop("change", axis = 1)

#TEST SET UP
year = 2016
age = 66
grate=0.02
earnings = 37700
