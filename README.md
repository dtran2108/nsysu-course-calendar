# NSYSU Course Calendar Integration

## Task list
- [x] Set up Google Calendar API
- [ ] Implement user authentication via [selcrs.nsysu.edu.tw](https://selcrs.nsysu.edu.tw)
- [ ] Scrape necessary course information from [selcrs.nsysu.edu.tw](https://selcrs.nsysu.edu.tw)
- [ ] Integrate course import and smart notifications into Google Calendar
- [ ] Design login screen UI
- [ ] Build calendar preview interface
- [ ] Create smart notification configuration UI

## Overview:
Although NSYSU already has an official app, its calendar feature lacks detailed course descriptions. I find Google Calendar more convenient since it allows home screen widgets and customizable alerts. My project aims to integrate the NSYSU course syllabus into Google Calendar using Python, enhancing accessibility and planning efficiency.

## Key Features:
**1.	Automatic Course Import**

-	Fetch course schedules from [cu.nsysu.edu.tw](https://cu.nsysu.edu.tw) or [selcrs.nsysu.edu.tw](https://selcrs.nsysu.edu.tw) using web scraping.
-	Include details such as course name, weekly topics, and classroom locations.

> Example:
>	- Course: Programming Design
>	- Week 1 (2025/02/21): Introduction to Programming & Python Basics
>	- Room: IL PC01

**2.	Google Calendar Integration**

-	Students can log in using their **Student ID** and **password** through a simple GUI.
-	A preview window will display the full schedule before finalizing the import.
-	A "Generate" button will sync the data with Google Calendar.

**3.	Smart Notifications**

-	Automated reminders three weeks before midterms and finals to assist with exam preparation.
-	Customizable sequential alarms for better time management.

## Technology Stack:
-	`Python` for data scraping and processing
-	~~Pyglet~~ `Streamlit` for the GUI (Initially, I planned to use `Pyglet`, but I switched to `Streamlit` because I want the app to be accessible online, allowing anyone to use it without needing to install anything.)
-	`Google Calendar API` for event creation
