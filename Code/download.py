# imports
import requests
from PyPDF2 import PdfReader
import os
import shutil

# global variables
START_YEAR = 2013
END_YEAR = 2022
GP_ALL = ["QAT", "POR", "AME", "ARG", "ESP", "FRA", "ITA", "CAT", "NED", "GER", \
  "USA", "INP", "AUT", "CZE", "GBR", "RSM", "ARA", "JPN", "THA", "INA", "AUS", "MAL", "VAL", \
  "ANC", "STY", "EMI", "TER", "EUR", "DOH", "ALR"]  # double headers exclusive


def download_pdf(url, filename, datatype):
    """
    Downloads pdf from url and checks whether it's a valid pdf.
    Url, filename, and datatype are all strings.
    Datatype can only be either 'FP' or 'Race'.
    """

    # download
    response = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(response.content)

    # check
    try:
        PdfReader(filename)
        if datatype == 'Race':
            shutil.move(filename, f"../Data/Race/{filename}")
        elif datatype == 'FP':
            shutil.move(filename, f"../Data/FP/{filename}")
    except:
        os.remove(filename)

    return


# download all data
print("download start")
for year in range(START_YEAR, END_YEAR + 1):
    print(f"\n{year}")
    for gp in GP_ALL:
        print(gp)
        url_race = f"https://resources.motogp.com/files/results/{year}/{gp}/MotoGP/RAC/Classification.pdf"
        url_fp = f"https://resources.motogp.com/files/results/{year}/{gp}/MotoGP/FP4/Analysis.pdf"
        filename_race = f"{year}-{gp}-RAC.pdf"
        filename_fp = f"{year}-{gp}-FP4.pdf"
        # note: for free practice, we're downloading FP4 only

        download_pdf(url_race, filename_race, "Race")
        download_pdf(url_fp, filename_fp, "FP")

print("download complete")