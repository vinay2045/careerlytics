
import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Careerlytics.settings')
django.setup()

from resumeanalysis.models import Language, MockTest

def populate_languages():
    print("Populating languages...")
    
    languages_data = [
        {
            'name': 'Python',
            'key': 'python',
            'description': 'Core Python, Django, Flask, NumPy',
            'icon': 'code',
            'color': 'blue'
        },
        {
            'name': 'Java',
            'key': 'java',
            'description': 'Core Java, Spring, Hibernate, JUnit',
            'icon': 'coffee',
            'color': 'red'
        },
        {
            'name': 'JavaScript',
            'key': 'javascript',
            'description': 'ES6+, Node.js, React, Vue.js, TypeScript',
            'icon': 'javascript',
            'color': 'yellow'
        },
        {
            'name': 'C++',
            'key': 'cpp',
            'description': 'Core C++, STL, OOP, Memory Management',
            'icon': 'memory',
            'color': 'purple'
        }
    ]
    
    LANGUAGE_TESTS = {
        'python': [
            {
                'name': 'Python Core Programming',
                'file': 'python_core.txt',
                'description': 'Python syntax, data types, and core concepts',
                'difficulty': 'Beginner',
                'time': 40,
                'questions': 20
            },
            {
                'name': 'Python Advanced',
                'file': 'python_advanced.txt',
                'description': 'Advanced Python features, decorators, and metaprogramming',
                'difficulty': 'Advanced',
                'time': 60,
                'questions': 25
            },
            {
                'name': 'Python Web Development',
                'file': 'python_web.txt',
                'description': 'Flask, Django, and web frameworks',
                'difficulty': 'Intermediate',
                'time': 50,
                'questions': 20
            }
        ],
        'java': [
            {
                'name': 'Java Core Programming',
                'file': 'java_core.txt',
                'description': 'Java fundamentals, OOP, and core libraries',
                'difficulty': 'Intermediate',
                'time': 45,
                'questions': 20
            },
            {
                'name': 'Java Spring Framework',
                'file': 'java_spring.txt',
                'description': 'Spring Boot, dependency injection, and enterprise Java',
                'difficulty': 'Advanced',
                'time': 60,
                'questions': 25
            },
            {
                'name': 'Java Concurrency',
                'file': 'java_concurrency.txt',
                'description': 'Multithreading, concurrency, and performance',
                'difficulty': 'Advanced',
                'time': 55,
                'questions': 20
            }
        ],
        'javascript': [
            {
                'name': 'JavaScript ES6+',
                'file': 'javascript_es6.txt',
                'description': 'Modern JavaScript features, ES6+, and async programming',
                'difficulty': 'Intermediate',
                'time': 40,
                'questions': 20
            },
            {
                'name': 'Node.js & Express',
                'file': 'javascript_nodejs.txt',
                'description': 'Server-side JavaScript and Express framework',
                'difficulty': 'Intermediate',
                'time': 45,
                'questions': 20
            },
            {
                'name': 'React & Frontend',
                'file': 'javascript_react.txt',
                'description': 'React, hooks, and modern frontend development',
                'difficulty': 'Advanced',
                'time': 60,
                'questions': 25
            }
        ],
        'cpp': [
            {
                'name': 'C++ STL',
                'file': 'cpp_stl.txt',
                'description': 'Standard Template Library, containers, and algorithms',
                'difficulty': 'Intermediate',
                'time': 50,
                'questions': 20
            },
            {
                'name': 'C++ Advanced',
                'file': 'cpp_advanced.txt',
                'description': 'Advanced C++, templates, and performance optimization',
                'difficulty': 'Advanced',
                'time': 60,
                'questions': 25
            },
            {
                'name': 'C++ System Programming',
                'file': 'cpp_system.txt',
                'description': 'System programming, memory management, and low-level concepts',
                'difficulty': 'Advanced',
                'time': 55,
                'questions': 20
            }
        ]
    }
    
    for lang_data in languages_data:
        language, created = Language.objects.update_or_create(
            key=lang_data['key'],
            defaults={
                'name': lang_data['name'],
                'description': lang_data['description'],
                'icon': lang_data['icon'],
                'color': lang_data['color']
            }
        )
        print(f"{'Created' if created else 'Updated'} language: {language.name}")
        
        # Add tests for this language
        if language.key in LANGUAGE_TESTS:
            for test_info in LANGUAGE_TESTS[language.key]:
                # Change .txt to .json
                file_name = test_info['file'].replace('.txt', '.json')
                
                MockTest.objects.update_or_create(
                    language=language,
                    name=test_info['name'],
                    defaults={
                        'file_name': file_name,
                        'questions_count': test_info['questions'],
                        'time_limit': test_info['time'],
                        'difficulty': test_info['difficulty'],
                        'description': test_info['description']
                    }
                )
                print(f"  - Added/Updated test: {test_info['name']}")

    print("Done!")

if __name__ == '__main__':
    populate_languages()
