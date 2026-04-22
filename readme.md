# CS 122 Final Project

# Project Title

The Loop

## Authors

- Sankalp Aswani - Data Visualization/Analysis
- Prateek Panda - Data Collection

## Project Description

The Loop is a Python-based application that gathers essential golf course
data, including hole yardages, course ratings, and slope ratings, to help
users understand the difficulty and accessibility of any course. Data is
sourced from the GolfCourseAPI, a free API with information on nearly
30,000 golf courses worldwide. Users can search for any course or club by
name and interact with the data through a clean graphical interface. The
application computes a Course Difficulty Index derived from slope ratings,
yardage, and par data, mapping course difficulty to what a recreational or
tournament player might expect to score. Whether you are a beginner
choosing your first course or a competitive player scouting for a
tournament, The Loop gives you the data you need to make an informed
decision on the course.

## Project Outline

### Interface Plan

The Loop will be built using Flask as a web interface with two pages. The
home screen allows users to search for a golf course by name, country, and
state, returning a list of matching results. The second page displays a
course overview including total yardage, par, course rating, and slope
rating, along with a yardage profile chart and a tee box recommendation
based on the user's handicap input.

### Data Collection and Storage Plan

Course data will be fetched from the GolfCourseAPI using Python's requests
library. Search results and course details will be stored locally as CSV
files, organized by course name, for use in analysis and visualization.

### Data Analysis and Visualization Plan

The application will analyze course data to recommend an appropriate tee
box based on the user's handicap and the slope and course ratings of each
tee. A yardage profile chart will be generated using matplotlib, displaying
hole-by-hole yardage colored by par value.