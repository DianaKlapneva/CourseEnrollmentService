from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

SERVICES = {
    'students': 'http://localhost:5001/graphql',
    'courses': 'http://localhost:5002/graphql',
    'enrollments': 'http://localhost:5003/graphql'
}

@app.route('/graphql', methods=['POST'])
def gateway():
    query = request.json.get('query', '').lower()

    if 'student' in query:
        url = SERVICES['students']
    elif 'course' in query:
        url = SERVICES['courses']
    elif 'enrollment' in query:
        url = SERVICES['enrollments']
    else:
        return jsonify({'error': 'Unknown service'}), 400
    
    resp = requests.post(url, json=request.json)
    return jsonify(resp.json())

@app.route('/')
def home():
    return '''
    <h1>GraphQL Gateway</h1>
    <p>Send POST requests to /graphql</p>
    <p>Services:</p>
    <ul>
        <li>Students: port 5001</li>
        <li>Courses: port 5002</li>
        <li>Enrollments: port 5003</li>
    </ul>
    '''

if __name__ == '__main__':
    app.run(port=5000, debug=True)