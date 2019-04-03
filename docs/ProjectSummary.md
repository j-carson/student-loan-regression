# Student Debt Linear Regression Study

## Design

### Need for Study
Are there certain types of colleges that put students more at risk for graduating with a lot of debt?

Americans owe over 1.5 trillion dollars in student loan debt according to the [NY Federal Reserve.](https://www.newyorkfed.org/microeconomics/hhdc.html)

These loans can have a significant impact on life after graduation per [Pew Research.](http://www.pewresearch.org/fact-tank/2017/08/24/5-facts-about-student-loans/) 

- About one-in-five employed adults ages 25 to 39 with at least a bachelor’s degree and outstanding student loans (21%) have more than one job. Those without student loan debt are roughly half as likely (11%) to hold multiple jobs.

- Only 27% of young college graduates with student loans say they are living comfortably, compared with 45% of college graduates of a similar age without outstanding loans.

You're a high school guidance counselor. What do you tell your students?


### Population

Four year, US-based, public and private universities.
### Target

Median debt at graduation, for students who received loans, per school. 

### Features

* College type (public, private non-profit)
* Number of undergraduates
* Admissions
	* Selective or noncompetitive admissions policy
* Makeup of students
	* Ethnicity
	* Low income (Pell-eligible students)
	* Percent of "traditional freshmen" (full-time, first-time, degree-seeking undergraduates versus transfers and other nontraditional students entering in the fall cohort)
* Cost of attendance
* College operating expenses 
	- Average faculty salary
	- Percent part time faculty
	- Cost of instruction per full-time student

#### Assignment requirements
To complete this assignment, at least 10 features and 1000 rows are required. At least some portion of the data must be scraped from the web using a tool like Selenium or requests.

## Data

### About College Scorecard

College Scorecard is the government data collected to analyze the financial impacts of going to college. Data is merged from multiple sources:

 - [National Center for Education Statistics Integrated Postsecondary Education System](https://nces.ed.gov/ipeds/), commonly referred to as IPEDS
 - [Federal Student Aid Data Center](https://studentaid.ed.gov/sa/data-center)
 - [Federal Student Aid Postsecondary Education Participant System](https://www2.ed.gov/offices/OSFAP/PEPS/dataextracts.html)
 - [National System Loan Data System](https://fp.ed.gov/nslds.html)
 - The US Treasury and Internal Revenue Service
 - Miscellaneous Department of Education data sets
 - US Census Bureau

Although College Scorecard API keys could not be requested due to the government shutdown, the raw CSV files were available [here](https://collegescorecard.ed.gov/data/).

Individual columns are grouped into categories including:

Category  | Meaning
:------------- | :-------------
|  Root | Primary keys
|  School | General characteristics of the school not covered by other categories
|  Academics | Academic offerings
|  Admissions | Admissions standards and rates
|  Student | Characteristics of new students enrolled
|  Cost | Tuition and cost of attendance related data
|  Aid | Financial aid related data
|  Repayment | Repayment and default rates of recent graduates
|  Completion | Graduation rates
|  Earnings | Earnings after graduation

Financial information about individual students is aggregated by school, and if any subcategory contains fewer than 30 students, that feature is  suppressed for that school is suppressed for privacy concerns. Full documentation is available [here](https://collegescorecard.ed.gov/assets/FullDataDocumentation.pdf)

### Loading and Cleaning College Scorecard Data

Downloading the CSV was easy, but making sense of a dataset with 7175 rows and 1899 columns (school year 2016-2017 data set) was much harder. I eventually settled on the approach of opening the data dictionary with the Pandas ```read_excel``` function and using that to programmatically tune my call to Pandas ```read_csv``` on the actual CSV file.

After reading in the data dictionary, I generated a list of all available columns. Then, I queried the data
dictionary for columns that were not relevant to my study and deleted them from the list of available columns. For example, the ```academics``` category is about what majors are offered and what percentage of students graduate with
each potential major, and I was not interested in using this information
as a feature in my model.

```python
# download data dictionary from https://collegescorecard.ed.gov/assets/CollegeScorecardDataDictionary.xlsx
datad = pd.read_excel( FILEDIR +"CollegeScorecardDataDictionary.xlsx", 
                      sheet_name="data_dictionary")


# take the dashes and spaces out of the excel column names (so python doesn't think I'm subtracting)
# and change to lower case (for consistency)
datad.columns = datad.columns.str.replace(" ", "_").str.replace("-", "_").str.lower()

# Collect the full list of column names, then drop names from 
# certain categories to make the list of columns we're keeping
subset_columns = list(datad.variable_name.dropna())

def drop_columns_by_category(category):
    cat_columns = datad.loc[datad.dev_category == category, 'variable_name']
    for c in cat_columns:
        subset_columns.remove(c)

drop_columns_by_category('academics')
```

I also used the data dictionary to find columns that Pandas should not attempt to type-convert to prevent 
errors on reading:

```python
these_are_strings = datad.loc[datad.variable_name.isin(subset_columns) &
                      datad.api_data_type.isin(['string', 'autocomplete']),
                    'variable_name']
                    
type_conversion = {}
for col in these_are_strings:
    type_conversion[col] = np.object
```

Finally, I read in the actual data, using Pandas arguments to skip the unwanted columns, to treat certain columns as strings, and to fill in NULLs for privacy suppressed columns.
            
```python
scorecard_data = pd.read_csv(filename,
                        keep_default_na=True, na_values="PrivacySuppressed", 
                        usecols=subset_columns,
                        dtype=type_conversion
                       )
```

Once the data was read in, I further suppressed schools that did not offer four year degrees as their predominant program, were for-profit schools, or which were online-only education. This left me a set of schools which I hoped would be more like comparing apples-to-apples. 

Once I dropped those rows, I dropped any columns that remained that had fewer than 400 observations as being too sparsely populated to work with. Many of these were columns that were entirely null-filled,  created for items collected in previous years but not collected in 2016-2017. Apparently no
columns are ever dropped from the database. 

At this point I had a more manageable dataset of 1819 rows and 171 columns. That was still a lot of potential features to 
look at, but much more manageable than the original dataset.


### About Collegedata.com

[Collegedata.com](https://collegedata.com) is a consumer website aimed at prospective college students focusing on college admissions and financial aid issues. I chose this website for the web scraping portion of the project because it had two potentially interesting features:

- **The percentage of parents receiving Parent PLUS loans.** Parent PLUS is an additional government loan available to families when the student has exhausted their eligibility for student loans. A high percentage of this type of loan would indicate that families are borrowing even more money than the College Scorecard data indicates. 
- **The financial aid methodology used by the college.** There are two primary financial aid methodologies, generally referred to as Federal and Institutional or as FAFSA and CSS/Profile. The methodology used by a school may affect how much financial aid a student is eligible for and whether that need is met with loans or grants.


### Loading and Cleaning Collegedata.com Data

Data was scraped from collegedata.com using a two step process.

#### Driving the Search Page with Selenium

The first step was to collect a list of all the colleges on website using the [search page](https://www.collegedata.com/cs/search/college/college_search_tmpl.jhtml). Using Selenium, I filled out the search page 108 times: for each state and US territory, I requested all of the public and then all of the private colleges. This stage was 99% automated. However, Selenium cannot click on a button that is not currently being displayed in the browser. The page is very tall and the search button I needed is at the bottom. In order to run the search loop, there is a spot in the notebook
with the comment "shrink page here!" The user needs to do the command-minus command to shrink the page to show the entire form from top to bottom, then run the remainder of the notebook will automatically search and download the results.

Each search result page is a table with links to the main college information page for that institution. I stashed the college name, city, state, and public or private information, plus the URL to the financial information page.

#### Scraping the Feature Data with Requests

Once the Selinium step was done, I used a second notebook to download the financial information page for each college. The financial information was scraped using the requests package which is much simpler than Selenium. 
I ran through the DataFrame from the Selenium step and for each URL, requested the page and scraped and stored the desired 
pieces of information. 

The connection used in the requests package would drop occasionally. When restarting, I did not want to revist pages I had 
already scraped. The financial aid methodology is displayed on the website as "Federal Methodology," "Institutional Methodology" or "Not Specified." It was never NULL. When restarting, I checked the Methodology column of the results
table for each URL. If it was still NULL, that meant I had not yet succesfully visited that page and the script restarted at that point. 

Once the data was scraped it was saved as a pickle file.

#### Collegedata.com data was not used in producing the final results

The results presented do not include any data from collegedata.com, due to missing data and difficulting in joining rows with the College Scorecard data.

* Missing data - The features of interest were not available for most of the colleges on the website. Of the 1794 colleges scraped, the Parent PLUS Loan feature was NULL for 1000 rows. The financial aid methodology row contained only 64 examples of the Instituional Methodoloy, which is not enough to use for a meaningful subset. I suspect most of the 140 NULLs in the methodology feature use the Institutional methodology, as that would align with the length of the [list of schools](https://profile.collegeboard.org/profile/ppi/participatingInstitutions.aspx) requiring the Profile form. However, I did not have time to investigate this. 

* Joining data - Despite not having enough data to do a full analysis, I thought I'd check to see if the subset of schools with PLUS information offered any potential insights. The scraped data did not include the code numbers used as primary keys in the government data. I attempted to use the python difflib ```closest_match``` function to match on school name and city. However, I was not able to join the data to a point where I was confident my results were correct. Chad suggested the ```fuzzywuzzy``` package as a substitute method, but I just ran out of time.


## Results

I only achieved an R-squared of .45. One problem is that the target feature (median debt at graduation) shows
that most students who borrow actually borrow the maximum amount allowed for four years of study. There's 
not as much variation in the target variable as there is in the features.

Both the lasso and ridge models agree that the following features are most important:

- Cost : Students attending more expensive schools borrow more
- Public universities : Students borrow more 
- Black-serving institutions : HBCU's and PBI's (historically black and predominantly black colleges) students
tend to take more loans 
- Hispanic serving institutions : Students borrow less
- Students at more selective schools also tend to have lower loans

Whether this is a property of the school (bigger financial aid budget) or a property of the student body (richer students would borrow less wherever they go) is not determined.

### Source code

[Source code is here](https://github.com/j-carson/student-loan-regression)
There is a readme file in the directory.  
