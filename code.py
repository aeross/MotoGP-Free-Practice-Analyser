# functions ---------------------------------------------------------------------------------------

def min_to_sec(laptime):
    # converts laptime format: from --'---.--- string type to seconds float type
    minsec = laptime.split("'")
    sec = round(int(minsec[0]) * 60 + float(minsec[1]), 3)
    return sec

def sec_to_min(sec):
    # converts laptime format: from seconds float type to --'---.--- string type
    min = 0
    while sec >= 60:
        sec -= 60
        min += 1
    sec = format(round(sec, 3), ".3f")
    laptime = str(min) + "'" + str(sec).zfill(6)
    return laptime

# -------------------------------------------------------------------------------------------------

def motogp_fpanalyser(filename):
    # filename MUST be taken from the pdf file from the MotoGP website 
    # e.g. https://resources.motogp.com/files/results/2022/INA/MotoGP/FP4/Analysis.pdf
    # this code will most likely no longer work if they change the pdf format in the future

    # this section is *stolen* from stackoverflow, pdf reading using pymupdf
    import fitz

    with fitz.open(filename) as doc:
        text = ""
        for page in doc:
            text += page.get_text()

    # laptime is of format INT ' INT INT . INT INT INT (single digit, without whitespace).
    # in regex: '''\d'\d\d.\d\d\d'''
    # the laptime data is separated with the names of each rider.
    # in regex: '''[A-Z][a-z]+ [A-ZÑ]{2,}'''
    # the Ñ is because, you know, maverick vinales...this doesn't generalise to other riders having
    # other non-standard alphabetical names though.
    # another problem is it doesn't match when riders have two words on their last name (fabio di gi).
    # it also matches maufacturers' names, which is something that is not intended.

    import re
    riders = re.findall("[A-Z][a-z]+ [A-ZÑ]{2,}", text)
    data = re.split("[A-Z][a-z]+ [A-ZÑ]{2,}", text)  # text data from each rider

    all_lapt = []
    for rider in data:
        rider_lapt = re.findall("\d'\d\d.\d\d\d", rider) # all laptimes from each rider
        all_lapt.append(rider_lapt)

    fastest_lap = all_lapt[-1][0]
    fastest_lap_sec = min_to_sec(fastest_lap)
    threshold = fastest_lap_sec * 1.03

    from statistics import mean

    check_dupl = []  # see if there are any duplicate names for the riders
    lapt_summary = []
    for i in range(1, len(riders) + 1):
        if riders[i - 1] not in check_dupl:
            check_dupl.append(riders[i - 1])
            all_lapt_sec = []
            for laptime in all_lapt[i]:
                lapt_sec = min_to_sec(laptime)
                # laptimes faster than the fastest lap or slower than the slowest threshold will not be counted
                # threshold is fastest lap * 1.03 (I made this up, don't know if there is a better threshold)
                if (lapt_sec >= fastest_lap_sec) and (lapt_sec <= threshold):
                    all_lapt_sec.append(lapt_sec)
        else:
            # the duplicate names only happens when a rider set the fastest laptime
            # so proceed as usual, but discard the 1st encountered laptime
            for laptime in all_lapt[i][1:]:
                lapt_sec = min_to_sec(laptime)
                if (lapt_sec >= fastest_lap_sec) and (lapt_sec <= threshold):
                    all_lapt_sec.append(lapt_sec)
            continue
        try:
            # the regex matches manufacturers name as well as riders name
            # in the case it doesn't match the riders, there will be no laptime
            # the try except is used to avoid errors caused by no laptime
            avg_lapt = mean(all_lapt_sec)  # avg laptime
            best_lapt = min(all_lapt_sec)  # best laptime

            lapt_summary.append([avg_lapt, best_lapt])
        except:
            check_dupl.remove(check_dupl[-1])

    # put lists into dict and print outputs
    data = dict(zip(check_dupl, lapt_summary))
    sorted_data = dict(sorted(data.items(), key=lambda item: item[1]))
    count = 1
    for i in sorted_data:
        print(str(count) + ": " + str(i))
        print("average laptime: " + sec_to_min(sorted_data[i][0]))
        print("best laptime: " + sec_to_min(sorted_data[i][1]) + "\n")
        count += 1
    return
