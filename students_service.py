from flask import Flask, request, jsonify
from flask_cors import CORS 
import graphene
import psycopg2

app = Flask(__name__)
CORS(app)

try:
    conn = psycopg2.connect(
        host="localhost",
        database="education_db",
        user="postgres",
        password="123",
        port=5432
    )
    
except Exception as e:
    print(f"ошибка: {e}")
    conn = None

class Student(graphene.ObjectType):
    id = graphene.ID()
    firstName = graphene.String()
    lastName = graphene.String()
    email = graphene.String()

class Query(graphene.ObjectType):
    students = graphene.List(Student)
    
    def resolve_students(self, info):
        if not conn:
            return []
        cur = conn.cursor()
        cur.execute("SELECT id, first_name, last_name, email FROM students")
        rows = cur.fetchall()
        return [Student(id=str(r[0]), firstName=r[1], lastName=r[2], email=r[3]) for r in rows]

class CreateStudent(graphene.Mutation):
    class Arguments:
        firstName = graphene.String(required=True)
        lastName = graphene.String(required=True)
        email = graphene.String(required=True)
    
    student = graphene.Field(Student)
    
    def mutate(self, info, firstName, lastName, email):
        print(f"DEBUG: Creating {firstName} {lastName} {email}")
        if not conn:
            print("DEBUG: No connection")
            return None
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO students (first_name, last_name, email) VALUES (%s, %s, %s) RETURNING id",
                (firstName, lastName, email)
            )
            conn.commit()
            student_id = cur.fetchone()[0]
            print(f"DEBUG: Created id {student_id}")
            return CreateStudent(student=Student(id=str(student_id), firstName=firstName, lastName=lastName, email=email))
        except Exception as e:
            print(f"DEBUG ERROR: {e}")
            return None

class UpdateStudent(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        firstName = graphene.String()
        lastName = graphene.String()
        email = graphene.String()
    
    student = graphene.Field(Student)
    
    def mutate(self, info, id, firstName=None, lastName=None, email=None):
        if not conn:
            return None
        cur = conn.cursor()
        cur.execute(
            "UPDATE students SET first_name = COALESCE(%s, first_name), last_name = COALESCE(%s, last_name), email = COALESCE(%s, email) WHERE id = %s RETURNING *",
            (firstName, lastName, email, id)
        )
        conn.commit()
        row = cur.fetchone()
        if row:
            return UpdateStudent(student=Student(id=str(row[0]), firstName=row[1], lastName=row[2], email=row[3]))
        return None

class DeleteStudent(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    
    def mutate(self, info, id):
        if not conn:
            return DeleteStudent(success=False)
        cur = conn.cursor()
        cur.execute("DELETE FROM students WHERE id = %s", (id,))
        conn.commit()
        return DeleteStudent(success=cur.rowcount > 0)

class Mutation(graphene.ObjectType):
    createStudent = CreateStudent.Field()
    updateStudent = UpdateStudent.Field()
    deleteStudent = DeleteStudent.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

@app.route('/graphql', methods=['POST'])
def graphql():
    data = request.get_json()
    query = data.get('query', '')
    result = schema.execute(query)
    return jsonify(result.data)

if __name__ == '__main__':
    app.run(port=5001, debug=True)
