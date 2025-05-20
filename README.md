# NSYSU Course Calendar Integration

## Overview:
Although NSYSU already has an official app, its calendar feature lacks detailed course descriptions. I find Google Calendar more convenient since it allows home screen widgets and customizable alerts. My project aims to integrate the NSYSU course syllabus into Google Calendar using Python, enhancing accessibility and planning efficiency.

## Key Features:
1.	Automatic Course Import
o	Fetch course schedules from cu.nsysu.edu.tw or selcrs.nsysu.edu.tw using web scraping.
o	Include details such as course name, weekly topics, and classroom locations.
Example:
o	Course: Programming Design
o	Week 1 (2025/02/21): Introduction to Programming & Python Basics
o	Room: IL PC01
2.	Google Calendar Integration
o	Students can log in using their Student ID and password through a simple GUI.
o	A preview window will display the full schedule before finalizing the import.
o	A "Generate" button will sync the data with Google Calendar.
3.	Smart Notifications
o	Automated reminders three weeks before midterms and finals to assist with exam preparation.
o	Customizable sequential alarms for better time management.

## Technology Stack:
•	Python for data scraping and processing
•	Pyglet for the GUI 
•	Google Calendar API for event creation
This project will provide NSYSU students with a more user-friendly and feature-rich way to manage their academic schedules.
