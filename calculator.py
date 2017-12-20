# This program calculates the estimates monthly social security retirement
# benefit for primary earner retirees. The first goal is to set-up the
# basic, no-work set-up.

# First load package dependencies. Pandas should be sufficient for now
import pandas as pd

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

# Year - year of retirement
# Age - age at retirement
# Earnings - Either earnings at year prior to retirement or a stream of wages
#            assumed to go end with the year of retirement. A future version
#            might expand this to a dictionary where we allow values in
#            the stream to be tied to specific years.
# singleEarn - A flag indicating whether earnings is for the final year
#              or a stream. True is for a single year, false is for a stream.
# grate - The growth rate of the wages relative to the national average.

def calcSS(year, yearNow, age, earnings, singleEarn = True, grate = 0.02,
           myWS = ssParam):
     # If they put in a single year, we have to go backwords to age 18
     if singleEarn == True:
        earnings = calcStream(year, age, earnings, grate, myWS)

     # Merge the earnings data frame and the ssParam dataframe so everything
     # is in one year and only the working years are live
     myWS = myWS.merge(earnings, 'outer', left_index = True, right_index = True)

     # Calculate Indexing
     year60 = year - (age - 60)
     myWS.loc[year60:year, "Index"] = 1
     for i in range(myWS.index.min(), year):
          myWS.loc[i, "Index"] = myWS.loc[year60, "AWI"]/myWS.loc[i, "AWI"]
              
     # Determine actual earnings by comparing wage to maximum eligible earnings
     myWS["ActualEarn"] = myWS[["MaxEarn", "wage"]].min(axis = 1)

     # Index Earnings
     myWS["indexedEarning"] = myWS["ActualEarn"]*myWS["Index"]

     # Pull top 35 years of indexed earnings
     myWS_Top35 = myWS.nlargest(35, "indexedEarning")

     # AIME calculation
     AIME = myWS_Top35["indexedEarning"].sum()/420

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
     if yearNow != year:
          colaAdj = (1+myWS.loc[year+1:yearNow, "COLA"]/100).prod()
     else:
          colaAdj = 0
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

    # initialize wage column
    myWages = myWages.assign(wage = lambda x: 0)
    
    # put earnings for that year in the correct row for that column
    myWages.loc[year, "wage"] = earnings
    
    # loop through to put correct wages in the dataframe
    for i in range(year-1,year-(age-18)-1, -1):
        wageNY = myWages.loc[i+1, "wage"]
        changeTY = myWages.loc[i+1, "AWI"]/myWages.loc[i, "AWI"]
        myWages.loc[i, "wage"] = wageNY/((1+grate)*changeTY)

    return myWages[["wage"]]

#TEST SET UP
year = 2016
age = 66
grate=0.02
earnings = 40000

myStream = calcStream(year, age, earnings, grate, ssParam)
#myStream["wage"] = myStream["wage"]
print(calcSS(year, 2017, age, myStream, False, grate))
#print(myStream)
