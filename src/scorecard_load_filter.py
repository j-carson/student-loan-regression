"""
First step loading and cleaning - reads the raw College Scorecard CSV files and
drops columns that probably won't be needed in my model and rows that are not
schools that offer four year undergraduate degrees
"""

import pandas as pd
import numpy as np

# download from https://collegescorecard.ed.gov/data/
FILEDIR = "../data/"

scorecard_files = [ "MERGED2016_17_PP.csv"  ]
FILES = [ FILEDIR + f for f in scorecard_files ] 

# download data dictionary from https://collegescorecard.ed.gov/assets/CollegeScorecardDataDictionary.xlsx
datad = pd.read_excel( FILEDIR +"CollegeScorecardDataDictionary.xlsx", 
                      sheet_name="data_dictionary")

# take the dashes and spaces out of the excel column names (so python doesn't think I'm subtracting)
# and change to lower case (for consistency)
datad.columns = datad.columns.str.replace(" ", "_").str.replace("-", "_").str.lower()


# Collect the full list of column names, then drop names from 
# certain categories to make the list of columns we're keeping
subset_columns = list(datad.variable_name.dropna())

# Drop columns by category listed in the data dictionary
# dropping things not related to the goal of avoiding schools where 
# students take out large student loans
# -- repayment shows loan repayment and default rates
# -- academics shows the majors/programs offered by the college and what percent
#    of students graduate with that program
# -- completion columns are related to graduation rates
# -- earnings columns are related to earnings after graduation
def drop_columns_by_category(category):
    cat_columns = datad.loc[datad.dev_category == category, 'variable_name']
    for c in cat_columns:
        subset_columns.remove(c)
        
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
    
    # CCUGPROF = 
    # 5 Four-year, higher part-time
    # 6 Four-year, medium full-time, inclusive, lower transfer-in
    # 7 Four-year, medium full-time, inclusive, higher transfer-in
    # 8 Four-year, medium full-time, selective, lower transfer-in
    # 9 Four-year, medium full-time , selective, higher transfer-in
    # 10 Four-year, full-time, inclusive, lower transfer-in
    # 11 Four-year, full-time, inclusive, higher transfer-in
    # 12 Four-year, full-time, selective, lower transfer-in
    # 13 Four-year, full-time, selective, higher transfer-in
    # 14 Four-year, full-time, more selective, lower transfer-in
    # 15 Four-year, full-time, more selective, higher transfer-in
    fouryear = full_data.query('CCUGPROF >= 5 and CCUGPROF <= 15')
    fouryear = fouryear.drop(columns='PREDDEG')

    # and then public or non-profit
    # Control code are
    # 1 = Public
    # 2 = Private nonprofit
    # 3 = Private for-profit
    fouryear = fouryear.query('CONTROL != 3')
    
    # curroper == 0 means school has closed
    # closed schools don't update their data
    fouryear = fouryear.query('CURROPER != 0')
    fouryear = fouryear.drop(columns='CURROPER')
    
    # distance-only schools don't report as much data
    # drop it early (0 == not distance only, i.e. has a campus)
    fouryear = fouryear.query('DISTANCEONLY == 0')
    fouryear = fouryear.drop(columns='DISTANCEONLY')
    return fouryear


#
# read each file
#

file_contents = dict()
for f in FILES:
    file_contents[f] = read_scorecard(FILEDIR + f)

# This is filtering out columns that have little usable
# data, including fields that have become obsolete 
# over time
sparse_set = set()
for f in FILES:
    counts = file_contents[f].count()
    sparse_cols = counts[ counts < 400 ].index
    sparse_set.update(sparse_cols)
    
    
# Saves the subset data in a pickle file for faster processing
for f in FILES:
    file_contents[f] = file_contents[f].drop(columns=sparse_set)
    new_name = f.replace(".csv", ".pck").replace("PP", "subset")
    file_contents[f].to_pickle(FILEDIR + new_name)

