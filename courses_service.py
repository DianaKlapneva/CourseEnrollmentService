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

class Course(graphene.ObjectType):
    id = graphene.ID()
    title = graphene.String()
    credits = graphene.Int()
    teacher = graphene.String()

class Query(graphene.ObjectType):
    courses = graphene.List(Course)
    
    def resolve_courses(self, info):
        cur = conn.cursor()
        cur.execute("SELECT id, title, credits, teacher FROM courses")
        rows = cur.fetchall()
        return [Course(id=str(r[0]), title=r[1], credits=r[2], teacher=r[3]) for r in rows]

class CreateCourse(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        credits = graphene.Int(required=True)
        teacher = graphene.String(required=True)
    
    course = graphene.Field(Course)
    
    def mutate(self, info, title, credits, teacher):
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO courses (title, credits, teacher) VALUES (%s, %s, %s) RETURNING id",
            (title, credits, teacher)
        )
        conn.commit()
        course_id = cur.fetchone()[0]
        return CreateCourse(course=Course(id=str(course_id), title=title, credits=credits, teacher=teacher))

class UpdateCourse(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        title = graphene.String()
        credits = graphene.Int()
        teacher = graphene.String()
    
    course = graphene.Field(Course)
    
    def mutate(self, info, id, title=None, credits=None, teacher=None):
        cur = conn.cursor()
        cur.execute(
            "UPDATE courses SET title = COALESCE(%s, title), credits = COALESCE(%s, credits), teacher = COALESCE(%s, teacher) WHERE id = %s RETURNING *",
            (title, credits, teacher, id)
        )
        conn.commit()
        row = cur.fetchone()
        if row:
            return UpdateCourse(course=Course(id=str(row[0]), title=row[1], credits=row[2], teacher=row[3]))
        return None

class DeleteCourse(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    
    def mutate(self, info, id):
        cur = conn.cursor()
        cur.execute("DELETE FROM courses WHERE id = %s", (id,))
        conn.commit()
        return DeleteCourse(success=cur.rowcount > 0)

class Mutation(graphene.ObjectType):
    createCourse = CreateCourse.Field()
    updateCourse = UpdateCourse.Field()
    deleteCourse = DeleteCourse.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

@app.route('/graphql', methods=['POST'])
def graphql():
    data = request.get_json()
    query = data.get('query', '')
    result = schema.execute(query)
    return jsonify(result.data)

if __name__ == '__main__':
    app.run(port=5002, debug=True)