import pandas as pd
import numpy as np


FILEDIR = "../data/"

FILES = [  "MERGED2013_14_PP.csv",
           "MERGED2014_15_PP.csv",
           "MERGED2015_16_PP.csv",
           "MERGED2016_17_PP.csv" ]


# load the data dictionary 
datad = pd.read_excel( FILEDIR +"CollegeScorecardDataDictionary.xlsx", sheet_name="data_dictionary")


# take the dashes and spaces out of the excel column names (so python doesn't think I'm subtracting)
# and change to lower case (for consistency)
datad.columns = datad.columns.str.replace(" ", "_").str.replace("-", "_").str.lower()


# Collect the full list of column names, then drop names from 
# to make the list of columns we're keeping
subset_columns = list(datad.variable_name.dropna())


def drop_columns_by_category(category):
    cat_columns = datad.loc[datad.dev_category == category, 'variable_name']
    for c in cat_columns:
        subset_columns.remove(c)


# Drop columns by category listed in the data dictionary
# dropping things that happen after student decides to attend a college 
# -- repayment shows repayment and default rates
# -- academics shows the majors/programs offered by the college and what percent
#    of students graduate with that program
# -- completion columns are related to graduation rates
# -- earnings columns are related to earnings after graduation
drop_columns_by_category('repayment')
drop_columns_by_category('academics')
drop_columns_by_category('completion')
drop_columns_by_category('earnings')

assert(290 == len(subset_columns))

# that looks small enough to at least be manageable. 
# but pd.read_csv is getting confused in a few places
# One more trip to the data dictionary to tell pandas
# which columns to interpret as strings

these_are_strings = datad.loc[datad.variable_name.isin(subset_columns) &
                      datad.api_data_type.isin(['string', 'autocomplete']),
                    'variable_name']

type_conversion = {}
for col in these_are_strings:
    type_conversion[col] = np.object


def read_scorecard(filename):
    full_data = pd.read_csv(filename,
                        keep_default_na=True, na_values="PrivacySuppressed", 
                        usecols=subset_columns,
                        dtype=type_conversion
                       )
    # Pull out the four-year schools
    #
    # Predominant degree earned codes are
    # 0 = Not Classified
    # 1 = Certificate-granting
    # 2 = Associates-granting
    # 3 = Bachelor's-granting
    # 4 = Entirely graduate-degree granting

    fouryear = full_data.query('PREDDEG == 3')

    # and then public or non-profit
    # Control code are
    # 1 = Public
    # 2 = Private nonprofit
    # 3 = Private for-profit

    fouryear = fouryear.query('CONTROL != 3')
    return fouryear


#
# read each file
#

file_contents = dict()
for f in FILES:
    file_contents[f] = read_scorecard(FILEDIR + f)


# drop columns where we have less than 1000 observations
# a number of these are columns left over from changes in
# versions of the IPEDS survey

too_many_nulls = set()
for f in FILES:
    df = file_contents[f]
    too_sparse = df.columns[ df.count() < 1000 ]
    too_many_nulls.update(too_sparse)


for f in FILES:
    file_contents[f] = file_contents[f].drop(columns=too_many_nulls)


for f in FILES:
    new_name = f.replace(".csv", ".pck")
    file_contents[f].to_pickle(FILEDIR + new_name)

