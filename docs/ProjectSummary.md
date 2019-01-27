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
	* Freshman SAT score
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

Once the data was read in, I further suppressed schools that were not primarily four year institutions, were for-profit schools, or which were online-only education. This left me a set of schools which I hoped would be more like comparing apples-to-apples. 

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


## Algorithms

The following procedures from ```sklearn``` were used when creating and
tuning my model:

```
LinearRegression
train_test_split
LassoCV
RidgeCV
```
In addition to using the output of these models, I tried to keep my target customer (a high school guidance counselor) in mind. A heavily engineered
feature (college cost times the log of the number of undergraduates) would not be actionable for such a person. I tried to prefer simpler, stand-alone features wherever I could.

## Tools

In addition to ```sklearn``` above, I also used:

```
Selenium
Requests
Pandas
Seaborn
Matplotlib
```

## Communication

Slides are available in the github repository.

## Lessons Learned

### Data cleaning
I believe my project could have benefitted from additional data cleaning. I struggled for quite a while with web scraping. The CSV file was easy to 
download, but it was hard getting to get the number of columns 
down to a reasonable number, and I probably did not do enough to
look at the outliers in the rows. Looking at the last chart in the slide deck, I'm not sure
my model is finding a difference in publc and private universities versus
just chasing the outliers in the private university data. We have some 
unusual colleges, such as tuition-free Berea college and several niche institutions with fewer than 30 students. A cut-off of 500 to 1000 undergraduate students minimum would still include most of the places a high school guidance counselor might think of when a parent asks about "small colleges."

## Remaining questions

### Feature engineering

I spent a lot of time feature engineering before I ran my first linear models. I didn't quite get the point that the feature engineering was not to change how the data looked by itself, but how it looks when plotted  against the target variable. 
I also realized too late in the game  that the 
StandardScaler is doing a lot of the work for you under the covers.  I should have been plotting the output of 
StandardScaler versus the target as a better way of looking at heteroskedacity and whether feature engineering was necessary. . 

I still do not have a good feel for successful feature engineering. I chose (or not) the engineered features primarily 
by swapping them into the model and seeing what happened. Clearly as the number of features grows, trial and error would 
not cut it.  I need to learn how to better recognize where my model could benefit 
from engineering and apply it more strategically. 

### Ready, Fire, Aim

Project planning is extremely difficult in a bootcamp situation. Students are given

*  a hard deadline
*  using data we've never used before
*  using techniques we've never used before
*  while being trained on those techniques as we go along

Time managment under these circumstances is very difficult -- It's hard to know how long something you 
have never done before is going to take. It's hard to understand what it is you don't understand about what you
are doing. 

I have been reacting to hard deadlines (such as projects and pair programming assignments with something of 
a ready-fire-aim approach, "just jump in and do something quickly." 

I definitely hit a wall with this on this project and had to actually take an evening off from coding to go back through 
all my notes, powerpoints, and class Jupyter notebooks to find the "lay of the land" again. This cost me a ton
of project work time, but I needed it. I now feel like I understand
what was "supposed to happen" in a linear regression study if that didn't exactly happen this time.

However, I'm not sure my project management skills have grown from this 
experience. I mean, it's nice that you give us a deadline for an MVP, 
but how exactly do we recover from not  meeting that? 
There wasn't a way to just skip trying to figure out all my data columns and go
straight to a linear regression with a 1800 column data set. 

Also, lost all of my talk practice time by making last minute chart changes when I asked for feedback on my slides. 
I needed to keep a better track of how I spend those last couple of hours.

### Detecting volatility in model versions

So, one of the bugs I had when I was switching from the cross validation data to the holdout set -- all of a sudden 
one of my coefficients radically 
changed. I quickly found the bug -- I had
retrained with the holdout set instead of using only the training data. But
that coeffient must have had high variance at some point during the 
time I was running the different RidgeCV and LassoCV trials. I need to go back and figure out how to detect and remove coeffients that show a lot of 
volatility across the cross-validation tests. Perhaps it would have been
more obvious if I had been runnign the cross-validation tests manually
rather than having the CV-functions automate that step? 

### Future Work

- Learn how to use the ```fuzzywuzzy``` package
- Find a better source for the data that wasn't available on collegedata.com
- Rework the feature engineering and feature selection with what I understand now to and make sure I truly found the best 
linear model with the most predictive available features.
- Build project time management skills
