# student-loan-regression
A data science portfolio project

## Question
Are there certain colleges that put students more at risk for
graduating with a lot of debt?

## Motivation

- Americans owe over 1.5 trillion dollars in student loan debt according to the [NY Federal Reserve.](https://www.newyorkfed.org/microeconomics/hhdc.html)

- These loans can have a significant impact on life after graduation per [Pew Research.](http://www.pewresearch.org/fact-tank/2017/08/24/5-facts-about-student-loans/) 
   - About one-in-five employed adults ages 25 to 39 with at least a bachelor’s degree and outstanding student loans (21%) have more than one job. Those without student loan debt are roughly half as likely (11%) to hold multiple jobs. 
 
   - Only 27% of young college graduates with student loans say they are living comfortably, compared with 45% of college graduates of a similar age without outstanding loans.


## Methodology

To complete this assignment, at least 10 features and 1000 rows are required.


- **Population**: Four year, US-based, public and private universities.

- **Targets**: Average debt at graduation, percentage of parents taking PLUS loans.

- **Features**: 
    - College type (public, private)
    - Number of undergraduates
    - College location (city, rural, etc.) 
    - College state (may be too many categories?)
    - Acceptance rate
    - Draw rate. Draw rate is the yield divided by the admit rate, a measure of whether the school is a typical student's first choice
    - Freshman academic profile, SAT score and/or GPA. Using both may be too collinear?
    - Ethnicity of students
    - Percent international students
    - Cost of attendance, in-state
    - Cost of attendance, out-of-state (public universities)
    - Financial aid methodology (federal or institutional)
    - Financial aid percent need met
    - Financial aid average grant received
    - Average net price (may be collinear with above)
 

## Data

Data will be scraped from [collegedata.com](https://www.collegedata.com)

Robots.txt prohibits downloadng their pdf files but otherwise it looks like scraping is ok.


## Limits of study
1.	The average debt at graduation is a lagging indicator. The students who graduated in 2016 (the year available on collegedata.com) typically entered school four years earlier in 2012. College tuition and financial aid policies are always changing. There is some reason to believe that the rate of growth in student loans has tapered off in the past couple of years, for example [here.](https://ticas.org/sites/default/files/pub_files/classof2017.pdf)
2.	There are a number of csv’s available from the US Department of Education that would not meet the web scraping requirement, and due to the government shutdown may not be available. The most relevant may be the [College Scorecard dataset.](https://collegescorecard.ed.gov/data/) This dataset combines Department of Education, Federal Student Aid, National Direct Student Loan program, and Department of Treasury data and includes a number of features related to student loans. 
3.	Average debt at graduation does not apply to students who do not graduate. The students who take out loans and do not gradate have the worst of both worlds: They have the debt of a college student without the increase in salary that comes along with a college degree. The College Scorecard dataset (above) tracks student debt when the student separates from a college, whether that is by graduation, transfer, or dropping out.
4.	Debt can be a property of the student, rather than the school. Students from high income families are less likely to borrow than students from low income families no matter which college they choose. If there is time, there is data available from [Debt by Degrees](https://projects.propublica.org/colleges/) that could be scraped to focus specifically on debt incurred by low income students, defined as those receiving Pell grants. 
5.	The student loan crisis includes debt incurred at for-profit schools and in graduate school, as well as Parent PLUS loans which don’t count in the Scorecard data because the parent owes the money rather than the student. There is less data out there to scrape on these cases. 



