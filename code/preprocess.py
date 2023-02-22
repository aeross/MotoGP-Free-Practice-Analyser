# same thing as preprocess.ipynb, but instead of just one race weekend, we do
# the entire thing from the first race of 2013 to the last race of 2022

# imports
import tabula as tb
import pandas as pd
import numpy as np
import re
from os import listdir
from tqdm import tqdm

# global variables
START_YEAR = 2013
END_YEAR = 2022
GP_ALL = ["QAT", "POR", "AME", "ARG", "ESP", "FRA", "ITA", "CAT", "NED", "GER", \
  "USA", "INP", "AUT", "CZE", "GBR", "RSM", "ARA", "JPN", "THA", "INA", "AUS", "MAL", "VAL", \
  "ANC", "STY", "EMI", "TER", "EUR", "DOH", "ALR"]  # double headers exclusive

# -------------------------------------------------------------------------------------------------

# these are functions to convert laptime format
def lap_to_sec(lap):
    # converts laptime format: from --'---.--- string type to seconds float type
    minsec = lap.split("'")
    sec = round(int(minsec[0]) * 60 + float(minsec[1]), 3)
    return sec

def sec_to_lap(sec):
    # converts laptime format: from seconds float type to --'---.--- string type
    min = 0
    while sec >= 60:
        sec -= 60
        min += 1
    sec = format(round(sec, 3), ".3f")
    lap = str(min) + "'" + str(sec).zfill(6)
    return lap

# -------------------------------------------------------------------------------------------------

# preprocessing code, same as preprocessing.ipynb
def prep_race(filename):
    # filename needs to be string, e.g., "2013-AME-RAC.pdf"
    # it also needs to be a race pdf, otherwise...i don't even wanna know
    df = tb.read_pdf(filename, area = (120, 0, 500, 222), columns=[72, 78, 90, 110], pages = "1", silent=True)[0]
    df = df[pd.to_numeric(df['Pos'], errors='coerce').notnull()]
    df = df[['Pos', 'Unnamed: 2', 'Rider N']]
    df.rename(columns={'Unnamed: 2': 'Number', 'Rider N': 'Name'}, inplace=True)
    return df

# -------------------------------------------------------------------------------------------------

def prep_fp(filename):
    # same rules for filename apply here
    # this might look kinda messy, head over to preprocess.ipynb for more explanation bout the code

    # read pdf
    dfl = tb.read_pdf(filename, area = (20, 0, 730, 133), columns = [79], pandas_options = {'header': False}, pages = 'all', silent=True)
    dfr = tb.read_pdf(filename, area = (20, 318, 730, 399), columns = [340], pages = 'all', silent=True)
    combine_df = []
    for i in range(len(dfl)):
        combine_df.append(dfl[i])
        combine_df.append(dfr[i])
    df = pd.DataFrame(np.concatenate(combine_df, axis=0), columns=dfl[0].columns)
    
    # remove unnecessary values
    df.rename(columns={df.columns[0]: 'Lap Number', df.columns[1]: 'Lap Time'}, inplace=True)
    df['Lap Number'].replace('^([^0-9]*)$', '', regex=True, inplace=True) 
    df['Lap Number'].replace('', np.nan, inplace=True) 
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)

    # get rider number
    _temp = pd.to_numeric(df['Lap Number'], errors='coerce')
    riders = df[_temp.isna()].copy()
    riders['Lap Time'].replace('\D+', '', regex=True, inplace=True) 
    riders['Lap Time'].replace('', np.nan, inplace=True)
    riders.dropna(inplace=True)

    # get rider laptime
    rider_number = riders['Lap Time']
    rider_index = riders.index
    laps = df['Lap Time']
    k = 0
    laps_list = [[] for i in range(len(rider_index))]
    for i in range(1, len(laps)):
        if i in rider_index:
            k += 1
        elif re.search(r"\d{0,2}'\d\d\.\d\d\d.*", laps[i]):
            laps_list[k].append(laps[i])
    df = pd.DataFrame(laps_list).transpose()
    df.columns = rider_number
    df.drop(0, inplace=True)

    # remove invalid laps
    row_len = df.shape[0]
    col_len = df.shape[1]
    pit = False
    for i in range(col_len):
        for j in range(row_len):
            laptime = df.iat[j, i]
            if laptime == None:
                break
            if "P" in laptime:
                pit = True
                df.iat[j, i] = None
            elif pit:
                df.iat[j, i] = None
                pit = False
            elif "*" in laptime:
                df.iat[j, i] = None
            else:
                df.iat[j, i] = lap_to_sec(laptime)

    # remove laps above threshold
    minimum_lap = df.min(skipna=True)
    threshold = minimum_lap * 1.02
    df = df[df <= threshold]

    # find average and sort by ascending laptime
    df = df.mean().sort_values().reset_index()
    df.rename(columns={"Lap Time": "Number", 0: "Lap Time"}, inplace=True)

    return df

# -------------------------------------------------------------------------------------------------

def merge_fp_and_race(fp, race):
    # merges fp and race data
    fp = fp[fp["Number"].isin(race["Number"])]
    fp = fp[fp["Number"].notna()].reset_index()

    race = race[race["Number"].isin(fp["Number"])]
    race = race[race["Number"].notna()].reset_index()

    final = pd.DataFrame({"fp": fp["Number"], "race": race["Number"]})
    return final

# -------------------------------------------------------------------------------------------------

# next step is to save the dataframe as csv
# the data will be saved as "YYYY-ABC.csv" (ABC is the GP code)
FILENAME_LEN = 8
races = listdir("../Data/Race")
fps = listdir("../Data/FP")
# there are situations where the fp exists but the race doesn't exist, or, the race exists but not fp.
# this is probably because of the conditions at that time, the fp or race was cancelled.
# hence, we need to remove them out of the data.
fps = [i[:8] for i in fps]
races = [i[:8] for i in races]
data = [i for i in races if i in fps]

for i in tqdm(range(1, len(data))):  # start at 1 to skip gitkeep
    try:
        race = prep_race(f"../Data/Race/{data[i]}-RAC.pdf")
    except:
        # this is due to the wacky unstructured format the way MotoGP stores their data
        # especially the free practice...my current pdf scraping method might not perfectly
        # get all of them, and it's alright since it still gets most of them
        print("\nrace" + data[i])
        continue
    try:
        fp = prep_fp(f"../Data/FP/{data[i]}-FP4.pdf")
    except:
        # we'll just print the failed pdf scraping, and discard the data for future uses
        print("fp" + data[i])
        continue
    merge_fp_and_race(fp, race).to_csv(f"../Data/{data[i][:FILENAME_LEN]}.csv")

