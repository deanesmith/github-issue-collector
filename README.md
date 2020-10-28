# github-issue-collector

Used to aggregate github issues, pull requests, and releases in to a normalized postgres database for analysis.

Prerequisites

- Local or remote access to a postgres database
- Python 3.7 or greater (note older versions may be compatible)

Get Started

- Clone this project locally
- Connect to your postgres database 
- Create the ghissues schema by executing the pg-ghissues-schema.sql file in the root directory of your local github-issue-collector project
- Edit the repos.json file in the root directory of your local github-issue-collector project to include the projects that you want to collect data from.  A sample org/project is provided.
