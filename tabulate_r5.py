import json
import os
import pandas
import re
import sys
import warnings
from datetime import datetime
from glob import glob

warnings.simplefilter(action='ignore', category=FutureWarning)

ABCD_JSON         = 'ABCD_participants.json'
SELECTIONS_FILE   = 'selections.txt'
ABCD_RELEASE_CSVS_GLOB = '/data/ABCD_DSST/ABCD_BIDS/tabulated_data/release5/core/*/*.csv'
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
survey_field_dict = {'abcd_y_lt': ['interview_age']}
for survey_file in sorted(glob(ABCD_RELEASE_CSVS_GLOB)):
    print(survey_file)
    survey = os.path.basename(survey_file).split('.')[0]
    columns = pandas.read_csv(survey_file, low_memory=False).columns
    if len(selections) == 0:
        break
    poppers = []
    for i, field in enumerate(selections):
        if field == 'interview_age':
            continue
        # @TODO: Add error-checking logic for invalid field names

        # # the LongName always starts with the survey then ' | ' then the field name
        # survey = datadict[field]['LongName'].split(' | ')[0]
        if survey not in survey_field_dict:
            survey_field_dict[survey] = []
        if field in columns:
            survey_field_dict[survey].append(field)
            STARTER_JSON[field] = datadict[field]
            poppers.append(i)
    for i in sorted(poppers, reverse=True):
        selections.pop(i)

# crawl through the release files and collect the data
for i, survey in enumerate(survey_field_dict):
    survey_fullpath = glob(f'/data/ABCD_DSST/ABCD_BIDS/tabulated_data/release5/core/*/{survey}.csv')[0]
    df = pandas.read_csv(survey_fullpath, low_memory=False)

    if i == 0:
        data = df[['src_subject_id', 'eventname']]

    for j, field in enumerate(survey_field_dict[survey]):
        print(datetime.now(), 'Merging field', str(i+1), ':', field)
        data = pandas.merge(data, df[['src_subject_id', 'eventname', field]], how='outer', on=['src_subject_id', 'eventname'])

# print(datetime.now(), 'Collapsing duplicate interview_age columns (this step is slow)')

# # # start interview_age as a single column duplicate
# # data['interview_age'] = data['interview_age'].loc[:,~data['interview_age'].columns.duplicated()]

# # "merge" to fix all the interview_age duplicated columns
# for i, row in enumerate(data[[column for column in data.columns if 'interview_age' in column]].values):
#     numset = set([num for num in row if num % 1 == 0])
#     number = list(numset)[0]
#     data['interview_age'][i] = number

# # drop all the duplicate interview_age columns
# data = data.drop(columns=[column for column in data.columns if 'interview_age' in column and column != 'interview_age'])

# reorder the column names
essentials = ['src_subject_id', 'eventname', 'interview_age']
data = data.reindex(columns=essentials+list([col for col in data.columns if col not in essentials]))

# correct datatypes and fill empties/NaNs
for field in data.columns:
    if field not in ['src_subject_id', 'eventname']:
        if field in ['interiview_age', 'demo_sex_v2', 'ehi_y_ss_scoreb']:
            data[field] = data[field].fillna(-999)
            data[field] = data[field].astype(int)
        # elif STARTER_JSON[field]['DataType'] == 'Integer':
        #     data[field] = data[field].fillna(-999)
        #     data[field] = data[field].astype(int)
        # elif STARTER_JSON[field]['DataType'] == 'Float':
        #     data[field] = data[field].fillna(-999.0)
        #     data[field] = data[field].astype(float)

data.rename(columns={
    'src_subject_id': 'participant_id',
    'eventname': 'session_id',
    'site_id_l': 'site_id',
    'interview_age': 'age',
    'demo_sex_v2': 'sex',
    'ehi_y_ss_scoreb': 'handedness'
    }, inplace=True)

data['session_id'].replace({
    'baseline_year_1_arm_1': 'ses-baselineYear1Arm1',
    '2_year_follow_up_y_arm_1': 'ses-2YearFollowUpYArm1',
    '4_year_follow_up_y_arm_1': 'ses-4YearFollowUpYArm1',
    '6_year_follow_up_y_arm_1': 'ses-6YearFollowUpYArm1'
    }, inplace=True)

data = data[data['session_id'].isin(['ses-baselineYear1Arm1', 'ses-2YearFollowUpYArm1', 'ses-4YearFollowUpYArm1', 'ses-6YearFollowUpYArm1'])]

data['session_id'] = pandas.Categorical(data['session_id'], [
    'ses-baselineYear1Arm1',
    'ses-2YearFollowUpYArm1',
    'ses-4YearFollowUpYArm1',
    'ses-6YearFollowUpYArm1'
    ])

data['sex'].replace({
    1: 'male',
    2: 'female',
    3: 'other',
    4: 'other',
    777: 'n/a',
    999: 'n/a'
    }, inplace=True)

data['handedness'].replace({
    1: 'right',
    2: 'left',
    3: 'ambidextrous'
    }, inplace=True)

data.sort_values(by=['participant_id', 'session_id'], inplace=True)

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
        cleaned_int_line = re.sub(r'([0-9])\.0(\n|\t)', r'\1\2', line_fixed)
        na_line = re.sub(r'\t(\t|$)', r'\tn/a\1', cleaned_int_line)
        t.write(na_line)

# remove the temporary file
os.remove(os.path.join(OUTPUT_DIR, OUTPUT_PREFIX + '.tsv.temp'))
