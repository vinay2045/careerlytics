import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Careerlytics.settings')
django.setup()

from resumeanalysis.models import Role, MockTest

ROLE_TESTS = {
    'frontend': [
        {
            'name': 'HTML & CSS Basics',
            'file': 'frontend_html_css.txt',
            'questions': 30,
            'time': 45,
            'difficulty': 'Beginner',
            'description': 'Test your knowledge of HTML5 and CSS3 fundamentals'
        },
        {
            'name': 'JavaScript Fundamentals',
            'file': 'frontend_js.txt',
            'questions': 40,
            'time': 60,
            'difficulty': 'Intermediate',
            'description': 'Core JavaScript concepts, ES6+, and DOM manipulation'
        },
        {
            'name': 'React Framework',
            'file': 'frontend_react.txt',
            'description': 'React components, hooks, state management, and best practices',
            'difficulty': 'Advanced',
            'time': 60,
            'questions': 30
        }
    ],
    'backend': [
        {
            'name': 'Django Framework',
            'file': 'backend_django.txt',
            'description': 'Django web framework, ORM, and best practices',
            'difficulty': 'Intermediate',
            'time': 45,
            'questions': 20
        },
        {
            'name': 'Node.js Backend',
            'file': 'backend_nodejs.txt',
            'description': 'Node.js, Express.js, and server-side JavaScript',
            'difficulty': 'Intermediate',
            'time': 45,
            'questions': 20
        },
        {
            'name': 'Database Design',
            'file': 'backend_database.txt',
            'description': 'SQL, NoSQL, database design and optimization',
            'difficulty': 'Advanced',
            'time': 60,
            'questions': 25
        }
    ],
    'devops': [
        {
            'name': 'Docker & Containers',
            'file': 'devops_docker.txt',
            'description': 'Docker, containerization, and orchestration',
            'difficulty': 'Intermediate',
            'time': 40,
            'questions': 20
        },
        {
            'name': 'CI/CD Pipeline',
            'file': 'devops_cicd.txt',
            'description': 'Continuous integration and deployment practices',
            'difficulty': 'Advanced',
            'time': 50,
            'questions': 25
        },
        {
            'name': 'Cloud Infrastructure',
            'file': 'devops_cloud.txt',
            'description': 'AWS, Azure, and cloud deployment strategies',
            'difficulty': 'Advanced',
            'time': 60,
            'questions': 30
        }
    ],
    'datascience': [
        {
            'name': 'Python for Data Science',
            'file': 'datascience_python.txt',
            'description': 'NumPy, Pandas, Matplotlib, and data analysis',
            'difficulty': 'Intermediate',
            'time': 50,
            'questions': 20
        },
        {
            'name': 'Machine Learning',
            'file': 'datascience_ml.txt',
            'description': 'Scikit-learn, TensorFlow, and ML algorithms',
            'difficulty': 'Advanced',
            'time': 60,
            'questions': 25
        },
        {
            'name': 'Data Visualization',
            'file': 'datascience_viz.txt',
            'description': 'Data visualization techniques and tools',
            'difficulty': 'Intermediate',
            'time': 45,
            'questions': 20
        }
    ]
}

roles_data = [
    {
        'name': 'Frontend Developer',
        'key': 'frontend',
        'description': 'HTML, CSS, JavaScript, React, Vue.js',
        'icon': 'web',
        'color': 'blue'
    },
    {
        'name': 'Backend Developer',
        'key': 'backend',
        'description': 'Python, Java, Node.js, Databases, APIs',
        'icon': 'dns',
        'color': 'green'
    },
    {
        'name': 'DevOps Engineer',
        'key': 'devops',
        'description': 'Docker, Kubernetes, CI/CD, AWS, Azure',
        'icon': 'cloud',
        'color': 'purple'
    },
    {
        'name': 'Data Scientist',
        'key': 'datascience',
        'description': 'Python, ML, Statistics, Data Analysis',
        'icon': 'analytics',
        'color': 'orange'
    }
]

for role_info in roles_data:
    role, created = Role.objects.get_or_create(
        key=role_info['key'],
        defaults={
            'name': role_info['name'],
            'description': role_info['description'],
            'icon': role_info['icon'],
            'color': role_info['color']
        }
    )
    if created:
        print(f"Created role: {role.name}")
    else:
        print(f"Role already exists: {role.name}")

    # Add tests
    tests = ROLE_TESTS.get(role.key, [])
    for test_info in tests:
        # Change .txt to .json in file name
        file_name = test_info['file'].replace('.txt', '.json')
        
        test, created = MockTest.objects.update_or_create(
            role=role,
            name=test_info['name'],
            defaults={
                'file_name': file_name,
                'questions_count': test_info.get('questions', 20),
                'time_limit': test_info.get('time', 30),
                'difficulty': test_info.get('difficulty', 'Intermediate'),
                'description': test_info.get('description', '')
            }
        )
        if created:
            print(f"  Created test: {test.name}")
        else:
            print(f"  Updated test: {test.name}")

print("Done population.")
