# An NDA ABCD Release Tabulation Tool

This repository houses a utility to make BIDS TSV and JSON files out of ABCD Release data.  It is currently tested and working on the NIH `helix` system with the ABCD Release 4.0 data.

## Installation and Usage

You can copy all the following text in the code block and paste it directly into a terminal on the NIH `helix` system.  As long as you have access to `/data/ABCD_DSST/ABCD_BIDS/tabulated_data/release4`, this `tabulate.py` code will work.

```shell
# clone this repository
git clone https://github.com/ericearl/nda-abcd-tabulate.git

# change into the repository's directory
cd nda-abcd-tabulate

# load the python module
module load python

# make sure pandas is installed
python -m pip install pandas --user

# create the selected tabulated data
python tabulate.py
```

## Explanation

The `tabulate.py` code takes the `selections.txt` file as an input list of fields to create a JSON adn TSV out of (not including the defaults: `subjectkey`, `eventname`, and `interview_age`).

## `selections.txt`

Edit the `selections.txt` file in place to include only one field per line named after the name that appears in the `ABCD_participants.json` file in this same GitHub repository.  For example, a `selections.txt` file that contained this...

```
site
sex
```

... would create as output a TSV file with the five columns: `participant_id`, `eventname`, `interview_age`, `site`, and `sex`.

## Issues

Known or discovered issues with this repository's files or functionality should be reported [here in this repository's Issues page](https://github.com/ericearl/nda-abcd-tabulate/issues).  Some are already known and are a work in progress, such as:

1. Choose any file on the system as input instead of only `selections.txt`
2. Choose any folder on the system to output the BIDS TSV and JSON files instead of only here as `abcd.{tsv,json}`
3. Choose your own ABCD Release 4.0 folder as input for finding the folder of NDA ABCD Release TXT file data
4. Error-check and graceful fail for any and all mis-typed field selections
5. Suggest a similarly named field based on available fields if an incorrect field name is entered
6. Suppress expected and unconcerning warning messages

## Acknowledgment

Thanks to Kathy, Shau-Ming, Shane, Dustin, Adam, and the rest of the team for inspiring this improvement to the ABCD NDA tabulated data experience.  Work provided by Eric Earl and the NIMH Data Science & Sharing Team.
