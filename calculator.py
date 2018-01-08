# This program calculates the estimates monthly social security retirement
# benefit for primary earner retirees. The first goal is to set-up the
# basic, no-work set-up.

# First load package dependencies. Pandas should be sufficient for now
import pandas as pd
from scipy.optimize import minimize_scalar

# First read in the csv file with year maximum earnings and indexing factor
ssParam = pd.read_csv("calculationParam.csv", header = 0)

ssParam.index = ssParam["Year"]
ssParam = ssParam.drop("Year", axis = 1)

# Create a function to calculate average earnings
# In this intitial iteration, it will expect either a full list of earnings
# or a single year of earnings and a growth factor. The user will also need to
# provide an age at retirement and the year of retirement. At the moment
# the earliest year we have max earnings and indexing for are 1956, so the
# years of earnings can only go back to 1956. Will assume work starting at
# age 18.

# Year - year of retirement. Earnings dumped in year prior
# Age - age at retirement
# Earnings - Either earnings at year prior to retirement or a stream of wages
#            assumed to go end with the year of retirement. A future version
#            might expand this to a dictionary where we allow values in
#            the stream to be tied to specific years.
# grate - The growth rate of the wages relative to the national average.

def calcSS(year, yearNow, age, earnings, grate = 0,
           myWS = ssParam):

     # calculate earning stream. This function also
     # merges the final result with the parameter dataframe 
     myWS = calcStream(year-1, age, earnings, grate, myWS)

     # Calculate Indexing
     year60 = year - (age - 60)
     myWS.loc[year60:year, "Index"] = 1
     for i in range(myWS.index.min(), year60):
          myWS.loc[i, "Index"] = myWS.loc[year60, "AWI"]/myWS.loc[i, "AWI"]
              
     # Determine actual earnings by comparing wage to maximum eligible earnings
     myWS["ActualEarn"] = myWS[["MaxEarn", "wage"]].min(axis = 1)

     # Index Earnings
     myWS["indexedEarning"] = myWS["ActualEarn"]*myWS["Index"]

     # Pull top 35 years of indexed earnings
     myWS_Top35 = myWS.nlargest(35, "indexedEarning")

     # AIME calculation
     AIME = (myWS_Top35["indexedEarning"].sum()/420)//1

     # min years for bends
     bend1 = round(180*myWS.loc[year60, "AWI"]/myWS.loc[1977, "AWI"], 0)
     bend2 = round(1085*myWS.loc[year60, "AWI"]/myWS.loc[1977, "AWI"], 0)
                   
     # Obtain full retirement benefit
     AIME_R1 = min(AIME, bend1) * 0.9
     AIME_R2 = max(0, min(AIME, bend2)-bend1)*0.32
     AIME_R3 = max(0, AIME - bend2)*0.15
     full_ben = AIME_R1 + AIME_R2 + AIME_R3

     # Limitation, we assume everyone born Jan 1
     fullRetAge = myWS.loc[year-age, "FullRetAge"]
     nMonthsEarly = max(0, fullRetAge - age*12)
     nMonthsLate = max(0, age*12 -(fullRetAge))

     reduct = min(36, nMonthsEarly)*(5.0/9.0) + max(
                       0, nMonthsEarly - 36)*(5.0/12.0)
     inc = max(0, (min(age, 70) - 66))*0.08

     ben = full_ben + full_ben * (inc - reduct)/100

     # COLA Adjustment
     if year != (year60+2):
          colaAdj = (1+myWS.loc[(year60+2):year, "COLA"]/100).prod()
     else:
          colaAdj = 1
     ben = ben * colaAdj
     
     # right now only full benefit calculation is set up
     return ben
     

# calcStream is a helper function that projects wages backwards
# for a given person with reported earnings for a single year
# and a given wage. This obviously will smooth out wage changes,
# so we might want to consider a different method of obtaining
# estimated wages. This is currently set up to match the basic
# social security calculator. 
def calcStream(year, age, earnings, grate, myWages):

    earnings = earnings.loc[earnings.index[0]:year]
    # initialize wage column    
    # put earnings for that year in the correct row for that column
    myWages = myWages.merge(earnings, 'outer', left_index = True,
                            right_index = True)
    myWages.loc[range(myWages.index.min(),earnings.index[0]), "wage"] = 0
    # loop through to put correct wages in the dataframe
    for i in range(earnings.index[0]-1,year-(age-18)-1, -1):
        wageNY = myWages.loc[i+1, "wage"]
        changeTY = myWages.loc[i+1, "AWI"]/myWages.loc[i, "AWI"]
        myWages.loc[i, "wage"] = wageNY/((1+grate)*changeTY)

    return myWages

def findGrate(target, year, yearNow, age, earnings, myWS = ssParam):
     def f(grate):
          return abs(calcSS(year, yearNow, age, earnings, grate)-target)
     res =  minimize_scalar(f, bounds = (-0.1, 0.1), method = 'bounded')
     return res.x

#TEST SET UP
# These tests were run using https://www.ssa.gov/OACT/ProgData/retirebenefit1.html
year = 2018
age = 62
grate=0.02
earnings = pd.read_csv("exCase2.csv", header = 0)

earnings.index = earnings["Year"]
earnings = earnings.drop("Year", axis = 1)
print(earnings)
#target = 1514

#grate = findGrate(target, year, year, age, earnings)
#print(grate)

#myStream["wage"] = myStream["wage"]
print(calcSS(year, year, age, earnings, grate))
#print(calcSS(year, 2017, age, earnings, grate= 0.02))

