import json
import os
import pandas
from glob import glob

csvs = glob('C:\\Users\\earlea\\Desktop\\temp\\abcd-4.0-data-dictionaries\\*.csv')

with open('C:\\Users\\earlea\\Desktop\\repo\\brainblocks\\DatasetDocumentation\\ABCD\\ABCD_participants.json','w') as f:
    data_dict = {}
    for csv in csvs:
        basename = os.path.basename(csv).replace('.csv','')
        if os.stat(csv).st_size > 0:
            data = pandas.read_csv(csv)
        else:
            continue

        for i in range(data.shape[0]):
            # ignoring the repeated first 5 entries in every csv
            if i < 6:
                continue

            try:
                ShortName = str(data['ElementName'][i])
                LongName = basename + ' | ' + ShortName
            except:
                print('Skipping', str(i))
                continue

            try:
                Description = str(data['ElementDescription'][i])
                Notes = str(data['Notes'][i])
                if Notes != 'nan':
                    Description += ' | ' + Notes
            except:
                Description = None

            try:
                Notes = str(data['Notes'][i])
                if Notes != 'nan':
                    Levels = {}
                    semicolons = Notes.split(';')
                    if len(semicolons) > 1:
                        for semicolon in semicolons:
                            equals = semicolon.split('=')
                            if len(equals) == 2:
                                coding = str(equals[0].strip())
                                meaning = str(equals[1].strip())
                                Levels[coding] = meaning
                            else:
                                print('len(equals) != 2:', equals)
                    elif len(semicolons.split('=')) == 2:
                        coding, meaning = semicolons.split('=')
                        if coding != '' and meaning != '':
                            Levels[str(coding).strip()] = str(meaning).strip()
                        else:
                            print('len(semicolons) == 1:', semicolons)
                    else:
                        print(Notes)
                else:
                    Levels = None
            except:
                Levels = None

            try:
                DataType = str(data['DataType'][i])
            except:
                DataType = None

            try:
                ValueRange = str(data['ValueRange'][i])
                if ValueRange == 'nan':
                    ValueRange = None
            except:
                ValueRange = None

            data_dict[ShortName] = {}
            data_dict[ShortName]["LongName"] = LongName
            if Description:
                data_dict[ShortName]["Description"] = Description
            if DataType:
                data_dict[ShortName]["DataType"] = DataType
            if ValueRange:
                data_dict[ShortName]["ValueRange"] = ValueRange
            if Levels:
                data_dict[ShortName]["Levels"] = Levels

    f.write(json.dumps(data_dict, indent=4))
