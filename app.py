from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime
import random

app = Flask(__name__)

# Store courses in memory (you might want to use a database in production)
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

@app.route("/")
@app.route("/index")
def index():
	return render_template("index.html")

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

if __name__ == '__main__':
	app.run(debug=True)