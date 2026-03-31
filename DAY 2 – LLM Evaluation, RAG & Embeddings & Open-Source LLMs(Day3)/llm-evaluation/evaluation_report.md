# LLM Evaluation Report

## 1. Test Set (25 Questions)

| Question | Ground Truth |
|----------|--------------|
| What does the 'M' represent in Django’s MTV pattern? | Model, which represents the data-access layer. |
| What is the role of templates in Django? | Templates handle the presentation layer and define how data is displayed. |
| What does the 'V' represent in Django’s MTV pattern? | View, which contains business logic and connects models to templates. |
| What is a Django model? | A model is a Python class representing database structure and data. |
| What command is used to create a new Django app? | python manage.py startapp <app_name> |
| Where are database configurations stored in Django? | In the settings.py file. |
| What does DATABASE_ENGINE specify in Django settings? | It specifies which database backend to use. |
| What is SQLite in Django context? | A file-based database that does not require a separate database server. |
| What is a Django app? | A reusable package containing models, views, and related logic. |
| What does a Django project contain? | A collection of apps along with configuration settings. |
| What is the purpose of Python functions? | To encapsulate reusable blocks of code. |
| What is the __init__ function in Python classes? | It is a constructor method used to initialize objects. |
| What is a Python module? | A file containing Python code that can be imported and reused. |
| What is exception handling in Python? | A mechanism to handle runtime errors using try-except blocks. |
| What is PIP used for in Python? | It is used to install and manage Python packages. |
| Why does Django prefer defining models in Python instead of relying on database introspection? | Because introspection introduces overhead and may be inaccurate, while Python models improve performance and maintainability. |
| Why is Django considered an MTV framework instead of strict MVC? | Because Django handles the controller internally and emphasizes models, templates, and views. |
| Why is writing raw SQL in Django views considered a poor approach? | Because it introduces boilerplate code, reduces portability, and tightly couples the code to a specific database. |
| Why should models be kept in apps in Django? | Because Django requires models to reside within apps for proper organization and functionality. |
| Why are Python virtual environments useful? | They isolate dependencies and allow different projects to use different package versions. |
| Does Django natively support GraphQL without third-party libraries? | Not mentioned in the document. |
| Does the document describe deploying Django using Kubernetes? | Not mentioned in the document. |
| Does the Python document explain async/await concurrency in detail? | Not mentioned in the document. |
| Does the Django book cover microservices architecture patterns? | Not mentioned in the document. |
| Does the Python programming document include machine learning model training examples? | Not mentioned in the document. |

## 2. Results Table
| #  | Question                                             | Answer A                   | Answer B                    | Exact A | Exact B | Sim A | Sim B | Winner |
| -- | ---------------------------------------------------- | -------------------------- | --------------------------- | ------- | ------- | ----- | ----- | ------ |
| 1  | What does the 'M' represent in Django’s MTV pattern? | In Django's MTV pattern... | The 'M' represents Model... | Fail    | Fail    | 0.31  | 0.31  | A      |
| 2  | Role of templates?                                   | Not mentioned...           | Not mentioned...            | Fail    | Fail    | 0.30  | 0.30  | B      |
| 3  | What does 'V' represent?                             | Explanation...             | View...                     | Fail    | Fail    | 0.31  | 0.31  | A      |
| 4  | What is a Django model?                              | Class representing DB...   | Not defined...              | Fail    | Fail    | 0.33  | 0.30  | A      |
| 5  | Create Django app command?                           | Correct command            | Incorrect                   | Pass    | Fail    | 0.95  | 0.40  | A      |
| 6  | DB config location?                                  | settings file...           | settings.py...              | Fail    | Fail    | 0.50  | 0.52  | B      |
| 7  | DATABASE_ENGINE?                                     | Specifies DB...            | Specifies backend...        | Fail    | Fail    | 0.45  | 0.47  | A      |
| 8  | SQLite?                                              | Lightweight DB...          | Not mentioned...            | Fail    | Fail    | 0.55  | 0.20  | A      |
| 9  | Django app?                                          | Self-contained module...   | Similar...                  | Fail    | Fail    | 0.35  | 0.34  | A      |
| 10 | Django project?                                      | Contains apps...           | Incorrect...                | Fail    | Fail    | 0.31  | 0.20  | A      |
| 11 | Python functions?                                    | Not answered...            | Not answered...             | Fail    | Fail    | 0.11  | 0.12  | A      |
| 12 | `__init__`?                                          | Not answered...            | Not answered...             | Fail    | Fail    | 0.25  | 0.26  | B      |
| 13 | Python module?                                       | File with code...          | Incorrect...                | Fail    | Fail    | 0.40  | 0.15  | A      |
| 14 | Exception handling?                                  | Incorrect context...       | Correct...                  | Fail    | Fail    | 0.30  | 0.42  | A      |
| 15 | PIP?                                                 | Not answered...            | Not answered...             | Fail    | Fail    | 0.20  | 0.22  | A      |
| 16 | Models vs introspection?                             | Partial...                 | Better...                   | Fail    | Fail    | 0.45  | 0.47  | A      |
| 17 | MTV vs MVC?                                          | Correct-ish...             | Similar...                  | Fail    | Fail    | 0.50  | 0.50  | A      |
| 18 | Raw SQL bad?                                         | Partial...                 | Better...                   | Fail    | Fail    | 0.48  | 0.49  | A      |
| 19 | Models in apps?                                      | Reasoning...               | Better...                   | Fail    | Fail    | 0.49  | 0.50  | B      |
| 20 | Virtual envs?                                        | Weak...                    | Better...                   | Fail    | Fail    | 0.32  | 0.35  | A      |
| 21 | GraphQL support?                                     | Not mentioned              | Not mentioned               | Pass    | Pass    | 1.00  | 1.00  | Tie    |
| 22 | Kubernetes deploy?                                   | Not mentioned              | Not mentioned               | Pass    | Pass    | 1.00  | 1.00  | Tie    |
| 23 | Async/await?                                         | Not mentioned              | Not mentioned               | Pass    | Pass    | 1.00  | 1.00  | Tie    |
| 24 | Microservices?                                       | Not mentioned              | Not mentioned               | Pass    | Pass    | 1.00  | 1.00  | Tie    |
| 25 | ML examples?                                         | Not mentioned              | Not mentioned               | Pass    | Pass    | 1.00  | 1.00  | Tie    |

## 3. Summary
```
MODEL_A = "llama-3.1-8b-instant" 
MODEL_B = "llama-3.3-70b-versatile" 

Total Questions: 25
Wins A: 15 (60.0%)
Wins B: 5 (20.0%)
Ties: 5 (20.0%)
Overall Winner: Model A
```

## 4. Top 5 Failure Examples

1. **What is the purpose of Python functions?**
   - Reason: Low semantic similarity (0.113) and/or exact match failure.

2. **What does a Django project contain?**
   - Reason: Low semantic similarity (0.310) and/or exact match failure.

3. **What does the 'M' represent in Django’s MTV pattern?**
   - Reason: Low semantic similarity (0.313) and/or exact match failure.

4. **Why are Python virtual environments useful?**
   - Reason: Low semantic similarity (0.318) and/or exact match failure.

5. **What is a Django app?**
   - Reason: Low semantic similarity (0.351) and/or exact match failure.

