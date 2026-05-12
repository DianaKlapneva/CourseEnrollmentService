from flask import Flask, request, jsonify
from flask_cors import CORS
import graphene
import psycopg2

app = Flask(__name__)
CORS(app)

conn = psycopg2.connect(
    host="localhost",
    database="education_db",
    user="postgres",
    password="123",
    port=5432
)

class Enrollment(graphene.ObjectType):
    id = graphene.ID()
    studentId = graphene.Int()
    courseId = graphene.Int()
    status = graphene.String()

class Query(graphene.ObjectType):
    enrollments = graphene.List(Enrollment)
    
    def resolve_enrollments(self, info):
        cur = conn.cursor()
        cur.execute("SELECT id, student_id, course_id, status FROM enrollments")
        rows = cur.fetchall()
        return [Enrollment(id=str(r[0]), studentId=r[1], courseId=r[2], status=r[3]) for r in rows]

class CreateEnrollment(graphene.Mutation):
    class Arguments:
        studentId = graphene.Int(required=True)
        courseId = graphene.Int(required=True)
    
    enrollment = graphene.Field(Enrollment)
    
    def mutate(self, info, studentId, courseId):
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO enrollments (student_id, course_id, status) VALUES (%s, %s, 'active') RETURNING id",
            (studentId, courseId)
        )
        conn.commit()
        enrollment_id = cur.fetchone()[0]
        return CreateEnrollment(enrollment=Enrollment(id=str(enrollment_id), studentId=studentId, courseId=courseId, status='active'))

class UpdateEnrollment(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        status = graphene.String()
    
    enrollment = graphene.Field(Enrollment)
    
    def mutate(self, info, id, status=None):
        cur = conn.cursor()
        cur.execute(
            "UPDATE enrollments SET status = COALESCE(%s, status) WHERE id = %s RETURNING *",
            (status, id)
        )
        conn.commit()
        row = cur.fetchone()
        if row:
            return UpdateEnrollment(enrollment=Enrollment(id=str(row[0]), studentId=row[1], courseId=row[2], status=row[3]))
        return None

class DeleteEnrollment(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    
    def mutate(self, info, id):
        cur = conn.cursor()
        cur.execute("DELETE FROM enrollments WHERE id = %s", (id,))
        conn.commit()
        return DeleteEnrollment(success=cur.rowcount > 0)

class Mutation(graphene.ObjectType):
    createEnrollment = CreateEnrollment.Field()
    updateEnrollment = UpdateEnrollment.Field()
    deleteEnrollment = DeleteEnrollment.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

@app.route('/graphql', methods=['POST'])
def graphql():
    data = request.get_json()
    query = data.get('query', '')
    result = schema.execute(query)
    return jsonify(result.data)

if __name__ == '__main__':
    app.run(port=5003, debug=True)