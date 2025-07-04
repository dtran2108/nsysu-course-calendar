from flask import Flask, render_template, request, jsonify, Response
import json
from datetime import datetime, timedelta
import random
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import os
from flask import session, redirect, request
from dotenv import load_dotenv

load_dotenv()

# Allow OAuth2 to work over HTTP during development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Store courses in memory
courses = []

# Predefined set of opaque colors for courses
COURSE_COLORS = [
	'#BBDEFB',  # Blue
	'#D1C4E9',  # Purple
	'#C8E6C9',  # Green
	'#FFE0B2',  # Orange
	'#F8BBD0',  # Pink
	'#B2EBF2',  # Cyan
	'#DCEDC8',  # Lime
	'#FFECB3',  # Yellow
	'#C5CAE9',  # Indigo
	'#FFCDD2',  # Red
	'#E1BEE7',  # Deep Purple
	'#B3E5FC',  # Light Blue
	'#FFCCBC',  # Deep Orange
	'#D7CCC8',  # Brown
	'#CFD8DC',  # Blue Grey
]

# Google Calendar API configuration
SCOPES = ["https://www.googleapis.com/auth/calendar"]

IS_DESKTOP = os.getenv("IS_DESKTOP").lower() == "true"
DESKTOP_CREDENTIALS_PATH = os.getenv("DESKTOP_CREDENTIALS_PATH")
WEB_CREDENTIALS_PATH = os.getenv("WEB_CREDENTIALS_PATH")
PROD_WEB_CREDENTIALS_PATH = os.getenv("PROD_WEB_CREDENTIALS_PATH")
IS_PROD = os.getenv("PROD").lower() == "true"
REDIRECT_URI = os.getenv("PROD_REDIRECT_URI") if IS_PROD else os.getenv("LOCAL_REDIRECT_URI")

def get_google_calendar_service():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_secrets_file(
                PROD_WEB_CREDENTIALS_PATH if IS_PROD else WEB_CREDENTIALS_PATH,
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
            )
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            session['state'] = state
            return redirect(auth_url)

    return build("calendar", "v3", credentials=creds)

@app.route("/")
@app.route("/index")
def index():
	return render_template("index.html")

@app.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(
        PROD_WEB_CREDENTIALS_PATH if IS_PROD else WEB_CREDENTIALS_PATH,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(auth_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = Flow.from_client_secrets_file(
        PROD_WEB_CREDENTIALS_PATH if IS_PROD else WEB_CREDENTIALS_PATH,
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(authorization_response=request.url)
    
    creds = flow.credentials
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    
    return redirect('/calendar')

@app.route("/calendar")
def calendar():
	return render_template("calendar.html")

@app.route('/save_course', methods=['POST'])
def save_course():
	try:
		course_data = request.get_json()
		
		# Validate required fields
		required_fields = ['courseName', 'location', 'day', 'timeRange', 'periods']
		for field in required_fields:
			if field not in course_data:
				return jsonify({
					"status": "error",
					"message": f"Missing required field: {field}"
				}), 400

		# Assign a color to the course
		used_colors = {course.get('color') for course in courses}
		available_colors = [color for color in COURSE_COLORS if color not in used_colors]
		course_data['color'] = available_colors[0] if available_colors else random.choice(COURSE_COLORS)
		
		# Add timestamp for when the course was added
		course_data['added_at'] = datetime.now().isoformat()
		
		# Add the course to our storage
		courses.append(course_data)
		
		return jsonify({
			"status": "success",
			"message": "Course saved successfully",
			"course": course_data
		}), 200
		
	except Exception as e:
		app.logger.error(f"Error saving course: {str(e)}")
		return jsonify({
			"status": "error",
			"message": "An error occurred while saving the course"
		}), 500

@app.route('/update_course', methods=['POST'])
def update_course():
	try:
		course_data = request.get_json()
		app.logger.info(f"Received update request for course: {course_data}")
		
		# Validate required fields
		required_fields = ['courseName', 'location', 'day', 'timeRange', 'periods', 'courseId']
		for field in required_fields:
			if field not in course_data:
				return jsonify({
					"status": "error",
					"message": f"Missing required field: {field}"
				}), 400

		# Find and update the course
		course_found = False
		for i, course in enumerate(courses):
			if course['added_at'] == course_data['courseId']:
				# Keep the original color and timestamp
				course_data['color'] = course['color']
				course_data['added_at'] = course['added_at']  # Preserve the original timestamp
				courses[i] = course_data
				course_found = True
				break
		
		if not course_found:
			app.logger.error(f"Course not found with ID: {course_data['courseId']}")
			return jsonify({
				"status": "error",
				"message": "Course not found"
			}), 404

		app.logger.info(f"Course updated successfully: {course_data}")
		return jsonify({
			"status": "success",
			"message": "Course updated successfully",
			"course": course_data
		}), 200
		
	except Exception as e:
		app.logger.error(f"Error updating course: {str(e)}")
		return jsonify({
			"status": "error",
			"message": f"An error occurred while updating the course: {str(e)}"
		}), 500

@app.route('/delete_course', methods=['POST'])
def delete_course():
	try:
		data = request.get_json()
		app.logger.info(f"Received delete request for course: {data}")
		
		course_id = data.get('courseId')
		if not course_id:
			return jsonify({
				"status": "error",
				"message": "Course ID is required"
			}), 400

		# Find and remove the course
		course_found = False
		for i, course in enumerate(courses):
			if course['added_at'] == course_id:
				courses.pop(i)
				course_found = True
				break
		
		if not course_found:
			app.logger.error(f"Course not found with ID: {course_id}")
			return jsonify({
				"status": "error",
				"message": "Course not found"
			}), 404

		return jsonify({
			"status": "success",
			"message": "Course deleted successfully"
		}), 200
		
	except Exception as e:
		app.logger.error(f"Error deleting course: {str(e)}")
		return jsonify({
			"status": "error",
			"message": f"An error occurred while deleting the course: {str(e)}"
		}), 500

@app.route('/get_courses', methods=['GET'])
def get_courses():
	return jsonify(courses)

@app.route('/export_to_calendar', methods=['POST'])
def export_to_calendar():
    try:
        data = request.json
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        
        if not start_date or not end_date:
            return jsonify({'status': 'error', 'message': 'Missing required data'}), 400
        
        # Check if we have valid credentials
        if not os.path.exists("token.json"):
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
            
        service = get_google_calendar_service()
        calendar_id = 'primary'
        
        # Convert start_date to datetime for manipulation
        base_start_date = datetime.strptime(start_date, '%Y-%m-%d')
        
        # Create events for each course
        for course in courses:
            # Get the first and last time ranges to determine the full duration
            first_time_range = course['timeRange'][0]
            last_time_range = course['timeRange'][-1]
            
            # Extract start time from first range and end time from last range
            start_time = first_time_range.split('~')[0].strip()
            end_time = last_time_range.split('~')[1].strip()
            
            # Map days to numbers (0 = Monday, 1 = Tuesday, etc.)
            day_mapping = {
                'Monday': 0,
                'Tuesday': 1,
                'Wednesday': 2,
                'Thursday': 3,
                'Friday': 4
            }
            
            course_day = day_mapping[course['day']]
            base_day = base_start_date.weekday()  # 0 = Monday, 1 = Tuesday, etc.
            
            # Calculate days to add to reach the correct day of the week
            days_to_add = (course_day - base_day) % 7
            course_start_date = base_start_date + timedelta(days=days_to_add)
            
            # Format the adjusted start date
            adjusted_start_date = course_start_date.strftime('%Y-%m-%d')
            
            event = {
                'summary': course['courseName'],
                'location': course['location'],
                'description': f"Instructor: {course['instructor']}" if course.get('instructor') else '',
                'start': {
                    'dateTime': f"{adjusted_start_date}T{start_time}:00",
                    'timeZone': 'Asia/Taipei',
                },
                'end': {
                    'dateTime': f"{adjusted_start_date}T{end_time}:00",
                    'timeZone': 'Asia/Taipei',
                },
                'recurrence': [
                    f'RRULE:FREQ=WEEKLY;UNTIL={end_date.replace("-", "")}T235959Z;BYDAY={["MO", "TU", "WE", "TH", "FR"][course_day]}'
                ],
            }
            
            service.events().insert(calendarId=calendar_id, body=event).execute()
        
        return jsonify({'status': 'success', 'message': 'Courses exported to Google Calendar successfully'})
        
    except HttpError as error:
        return jsonify({'status': 'error', 'message': f'Google Calendar API error: {str(error)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
	app.run(debug=True)