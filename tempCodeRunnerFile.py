    students_query = students_query.filter(
                (Student.name.ilike(f'%{search}%')) |
                (Student.roll_number.ilike(f'%{search}%'))
            )