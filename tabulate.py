import json
import os
import pandas
import sys

# SELECTIONS_FILE = sys.argv[1]

ABCD_JSON         = 'ABCD_participants.json'
SELECTIONS_FILE   = 'selections.txt'
ABCD_RELEASE_TXTS = '/data/ABCD_DSST/ABCD_BIDS/tabulated_data/release4'
OUTPUT_DIR        = '.'
OUTPUT_PREFIX     = 'abcd'

STARTER_JSON = {
    "participant_id": {
        "Description": "BIDS-formatted NDA pGUID"
    },
    "eventname": {
        "Description": "Name of study visit in which the row's data took place"
    },
    "interview_age": {
        "Description": "Age of the participant at visit",
        "Units": "Months"
    }
}

with open(ABCD_JSON, 'r') as j:
    datadict = json.load(j)

with open(SELECTIONS_FILE, 'r') as f:
    selections = [line.rstrip('\n').strip(' ') for line in f.readlines()]

# collect surveys and fields
survey_field_dict = {}
for field in selections:
    # @TODO: Add error-checking logic for invalid field names

    # the LongName always starts with the survey then ' | ' then the field name
    survey = datadict[field]['LongName'].split(' | ')[0]
    if survey not in survey_field_dict:
        survey_field_dict[survey] = []
    survey_field_dict[survey].append(field)
    STARTER_JSON[field] = datadict[field]

# crawl through the release files and collect the data
for i, survey in enumerate(survey_field_dict):
    survey_fullpath = os.path.join(ABCD_RELEASE_TXTS, survey + '.txt')
    df = pandas.read_csv(survey_fullpath, sep='\t', header=0, skiprows=[1])

    if i == 0:
        data = df[['subjectkey', 'eventname']]

    for field in survey_field_dict[survey]:
        data = pandas.merge(data, df[['subjectkey', 'eventname', 'interview_age', field]], how='outer', on=['subjectkey', 'eventname'])

# start interview_age as a single column duplicate
data['interview_age'] = data['interview_age_x'].loc[:,~data['interview_age_x'].columns.duplicated()]

# "merge" to fix all the interview_age duplicated columns
for i, row in enumerate(data[[column for column in data.columns if 'interview_age' in column]].values):
    numset = set([num for num in row if num % 1 == 0])
    number = list(numset)[0]
    data['interview_age'][i] = number

# drop all the duplicate interview_age columns
data = data.drop(columns=['interview_age_x', 'interview_age_y'])

# reorder the column names
essentials = ['subjectkey', 'eventname', 'interview_age']
data = data.reindex(columns=essentials+list([col for col in data.columns if col not in essentials]))

# correct datatypes and fill empties/NaNs
for field in data.columns:
    if field not in ['subjectkey', 'eventname']:
        if 'interview_age' in field:
            data[field] = data[field].fillna(-999)
            data[field] = data[field].astype(int)
        elif STARTER_JSON[field]['DataType'] == 'Integer':
            data[field] = data[field].fillna(-999)
            data[field] = data[field].astype(int)
        elif STARTER_JSON[field]['DataType'] == 'Float':
            data[field] = data[field].fillna(-999.0)
            data[field] = data[field].astype(float)

data.rename(columns={'subjectkey': 'participant_id'})

# write out TSV and JSON files
data.to_csv(os.path.join(OUTPUT_DIR, OUTPUT_PREFIX + '.tsv.temp'), sep='\t', index=False)

with open(os.path.join(OUTPUT_DIR, OUTPUT_PREFIX + '.json'), 'w') as j:
    j.write(json.dumps(STARTER_JSON, indent=4))

with open(os.path.join(OUTPUT_DIR, OUTPUT_PREFIX + '.tsv.temp'), 'r')  as t:
    temp = t.readlines()

with open(os.path.join(OUTPUT_DIR, OUTPUT_PREFIX + '.tsv'), 'w') as t:
    for line in temp:
        line_without_999s = line.replace('-999.0', 'n/a').replace('-999', 'n/a')
        line_fixed = line_without_999s.replace('NDAR', 'sub-NDAR').replace('NDAR_INV', 'NDARINV')
        t.write(line_fixed)

# remove the temporary file
os.remove(os.path.join(OUTPUT_DIR, OUTPUT_PREFIX + '.tsv.temp'))
