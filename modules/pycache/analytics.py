import sqlite3, json

DB = 'placementpro.db'

ROLE_SKILLS = {
    'Data Analyst':        ['Python', 'SQL', 'PowerBI', 'Excel', 'Tableau', 'Statistics', 'Pandas'],
    'Software Engineer':   ['DSA', 'Java', 'Python', 'Git', 'SQL', 'System Design', 'OOP'],
    'Full Stack Developer':['HTML', 'CSS', 'React', 'Node.js', 'MongoDB', 'REST API', 'Git'],
    'DevOps Engineer':     ['Linux', 'Docker', 'Kubernetes', 'CI/CD', 'AWS', 'Jenkins', 'Bash'],
    'ML Engineer':         ['Python', 'Machine Learning', 'Deep Learning', 'TensorFlow', 'Pandas', 'NumPy', 'Statistics'],
}

RESOURCES = {
    # ── Core Programming ─────────────────────────────────────────────
    'Python':          {'platform': 'freeCodeCamp',        'url': 'https://www.freecodecamp.org/learn/scientific-computing-with-python/', 'hours': 20},
    'Java':            {'platform': 'Codecademy',           'url': 'https://www.codecademy.com/learn/learn-java', 'hours': 20},
    'OOP':             {'platform': 'GeeksforGeeks',        'url': 'https://www.geeksforgeeks.org/object-oriented-programming-oops-concept-in-java/', 'hours': 10},
    'DSA':             {'platform': 'LeetCode',             'url': 'https://leetcode.com/explore/learn/', 'hours': 40},
    'Git':             {'platform': 'GitHub Docs',          'url': 'https://docs.github.com/en/get-started/quickstart/git-and-github-learning-resources', 'hours': 10},
    'SQL':             {'platform': 'SQLZoo',               'url': 'https://sqlzoo.net/wiki/SQL_Tutorial', 'hours': 10},
    'Bash':            {'platform': 'The Odin Project',     'url': 'https://www.theodinproject.com/lessons/foundations-command-line-basics', 'hours': 8},
    'C':               {'platform': 'Learn-C.org',          'url': 'https://www.learn-c.org/', 'hours': 15},
    'C++':             {'platform': 'LearnCpp.com',         'url': 'https://www.learncpp.com/', 'hours': 20},

    # ── Web & Frontend ───────────────────────────────────────────────
    'HTML':            {'platform': 'MDN Web Docs',         'url': 'https://developer.mozilla.org/en-US/docs/Learn/HTML', 'hours': 8},
    'CSS':             {'platform': 'MDN Web Docs',         'url': 'https://developer.mozilla.org/en-US/docs/Learn/CSS', 'hours': 10},
    'React':           {'platform': 'React Docs',           'url': 'https://react.dev/learn', 'hours': 12},
    'Node.js':         {'platform': 'Node.js Docs',         'url': 'https://nodejs.org/en/learn/getting-started/introduction-to-nodejs', 'hours': 10},
    'REST API':        {'platform': 'freeCodeCamp',         'url': 'https://www.freecodecamp.org/news/rest-api-tutorial-rest-client-rest-service-and-api-calls-explained-with-code-examples/', 'hours': 8},
    'JavaScript':      {'platform': 'javascript.info',      'url': 'https://javascript.info/', 'hours': 20},
    'TypeScript':      {'platform': 'TypeScript Docs',      'url': 'https://www.typescriptlang.org/docs/', 'hours': 12},
    'Django':          {'platform': 'Django Docs',          'url': 'https://docs.djangoproject.com/en/stable/intro/tutorial01/', 'hours': 15},
    'Flask':           {'platform': 'Flask Docs',           'url': 'https://flask.palletsprojects.com/en/latest/tutorial/', 'hours': 10},

    # ── Data & Analytics ─────────────────────────────────────────────
    'Pandas':          {'platform': 'Kaggle Learn',         'url': 'https://www.kaggle.com/learn/pandas', 'hours': 8},
    'NumPy':           {'platform': 'NumPy Official',       'url': 'https://numpy.org/learn/', 'hours': 6},
    'Statistics':      {'platform': 'Khan Academy',         'url': 'https://www.khanacademy.org/math/statistics-probability', 'hours': 20},
    'Excel':           {'platform': 'Microsoft Support',    'url': 'https://support.microsoft.com/en-us/excel', 'hours': 8},
    'PowerBI':         {'platform': 'Microsoft Learn',      'url': 'https://learn.microsoft.com/en-us/training/powerplatform/power-bi', 'hours': 15},
    'Tableau':         {'platform': 'Tableau Training',     'url': 'https://www.tableau.com/learn/training', 'hours': 10},
    'Data Visualization': {'platform': 'Kaggle Learn',      'url': 'https://www.kaggle.com/learn/data-visualization', 'hours': 8},
    'EDA':             {'platform': 'Kaggle Learn',         'url': 'https://www.kaggle.com/learn/data-cleaning', 'hours': 6},

    # ── Machine Learning & AI ────────────────────────────────────────
    'Machine Learning':{'platform': 'Coursera – Andrew Ng', 'url': 'https://www.coursera.org/learn/machine-learning', 'hours': 30},
    'Deep Learning':   {'platform': 'fast.ai',              'url': 'https://course.fast.ai/', 'hours': 25},
    'TensorFlow':      {'platform': 'TensorFlow.org',       'url': 'https://www.tensorflow.org/tutorials', 'hours': 15},
    'Scikit-learn':    {'platform': 'Scikit-learn Docs',    'url': 'https://scikit-learn.org/stable/tutorial/index.html', 'hours': 10},
    'NLP':             {'platform': 'Hugging Face Course',  'url': 'https://huggingface.co/learn/nlp-course/chapter1/1', 'hours': 20},
    'Computer Vision': {'platform': 'fast.ai',              'url': 'https://course.fast.ai/', 'hours': 20},

    # ── Architecture & Design ────────────────────────────────────────
    'System Design':   {'platform': 'Educative.io',         'url': 'https://www.educative.io/blog/complete-guide-system-design-interview', 'hours': 20},
    'DBMS':            {'platform': 'GeeksforGeeks',        'url': 'https://www.geeksforgeeks.org/dbms/', 'hours': 12},
    'OS':              {'platform': 'GeeksforGeeks',        'url': 'https://www.geeksforgeeks.org/operating-systems/', 'hours': 15},
    'Computer Networks':{'platform': 'GeeksforGeeks',       'url': 'https://www.geeksforgeeks.org/computer-network-tutorials/', 'hours': 12},

    # ── DevOps & Cloud ───────────────────────────────────────────────
    'Linux':           {'platform': 'Linux Journey',        'url': 'https://linuxjourney.com/', 'hours': 12},
    'Docker':          {'platform': 'Docker Docs',          'url': 'https://docs.docker.com/get-started/', 'hours': 8},
    'Kubernetes':      {'platform': 'Kubernetes.io',        'url': 'https://kubernetes.io/docs/tutorials/kubernetes-basics/', 'hours': 12},
    'AWS':             {'platform': 'AWS Skill Builder',    'url': 'https://skillbuilder.aws/', 'hours': 20},
    'Jenkins':         {'platform': 'Jenkins Docs',         'url': 'https://www.jenkins.io/doc/tutorials/', 'hours': 8},
    'CI/CD':           {'platform': 'GitHub Actions',       'url': 'https://docs.github.com/en/actions/learn-github-actions', 'hours': 6},

    # ── Databases ────────────────────────────────────────────────────
    'MongoDB':         {'platform': 'MongoDB University',   'url': 'https://learn.mongodb.com/', 'hours': 8},
    'MySQL':           {'platform': 'MySQL Tutorial',       'url': 'https://www.mysqltutorial.org/', 'hours': 8},
    'PostgreSQL':      {'platform': 'PostgreSQL Tutorial',  'url': 'https://www.postgresqltutorial.com/', 'hours': 10},
}

# Fallback map for skills not in RESOURCES — maps to best known direct URL
FALLBACK_URLS = {
    'r':               'https://www.coursera.org/learn/r-programming',
    'matlab':          'https://www.mathworks.com/learn/tutorials/matlab-onramp.html',
    'spark':           'https://spark.apache.org/docs/latest/quick-start.html',
    'hadoop':          'https://hadoop.apache.org/docs/stable/hadoop-mapreduce-client/hadoop-mapreduce-client-core/MapReduceTutorial.html',
    'selenium':        'https://www.selenium.dev/documentation/webdriver/getting_started/',
    'spring boot':     'https://spring.io/guides/gs/spring-boot/',
    'graphql':         'https://graphql.org/learn/',
    'redis':           'https://redis.io/docs/get-started/',
    'firebase':        'https://firebase.google.com/docs/guides',
    'azure':           'https://learn.microsoft.com/en-us/azure/guides/developer/azure-developer-guide',
    'gcp':             'https://cloud.google.com/learn/training',
}

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def get_skill_gap(student_id, target_role):
    conn = get_db()
    profile = conn.execute('SELECT skills FROM student_profiles WHERE user_id=?', (student_id,)).fetchone()
    conn.close()

    student_skills = set(s.lower() for s in json.loads(profile['skills'])) if profile and profile['skills'] else set()
    required_skills = ROLE_SKILLS.get(target_role, [])

    have = []
    missing = []
    for skill in required_skills:
        if skill.lower() in student_skills:
            have.append(skill)
        else:
            # Look up in RESOURCES first, then FALLBACK_URLS, then GeeksforGeeks search
            resource = RESOURCES.get(skill)
            if not resource:
                fallback_url = FALLBACK_URLS.get(skill.lower())
                if fallback_url:
                    resource = {'platform': 'Official Docs', 'url': fallback_url, 'hours': 10}
                else:
                    # GeeksforGeeks search is more reliable than YouTube search
                    search_term = skill.replace(' ', '+')
                    resource = {
                        'platform': 'GeeksforGeeks',
                        'url': f'https://www.geeksforgeeks.org/search/?q={search_term}',
                        'hours': 10
                    }
            missing.append({'skill': skill, **resource})

    match_pct = int(len(have) / len(required_skills) * 100) if required_skills else 0
    return {
        'have': have,
        'missing': missing,
        'match_pct': match_pct,
        'required': required_skills
    }

def get_placement_stats():
    conn = get_db()
    total_students = conn.execute("SELECT COUNT(*) as c FROM users WHERE role='student'").fetchone()['c']
    total_drives   = conn.execute("SELECT COUNT(*) as c FROM drives").fetchone()['c']
    total_apps     = conn.execute("SELECT COUNT(*) as c FROM applications").fetchone()['c']
    selected       = conn.execute("SELECT COUNT(*) as c FROM applications WHERE status='selected'").fetchone()['c']

    branch_stats = conn.execute('''
        SELECT sp.branch, COUNT(*) as count FROM student_profiles sp GROUP BY sp.branch
    ''').fetchall()

    top_drives = conn.execute('''
        SELECT d.company, d.role, COUNT(a.id) as applicants
        FROM drives d LEFT JOIN applications a ON d.id=a.drive_id
        GROUP BY d.id ORDER BY applicants DESC LIMIT 5
    ''').fetchall()

    status_dist = conn.execute('''
        SELECT status, COUNT(*) as count FROM applications GROUP BY status
    ''').fetchall()

    conn.close()
    return {
        'total_students': total_students,
        'total_drives': total_drives,
        'total_apps': total_apps,
        'selected': selected,
        'placement_rate': round(selected/total_students*100, 1) if total_students else 0,
        'branch_stats': [dict(r) for r in branch_stats],
        'top_drives': [dict(r) for r in top_drives],
        'status_dist': [dict(r) for r in status_dist],
    }

def evaluate_profile(student_id):
    conn = get_db()
    profile = conn.execute('SELECT * FROM student_profiles WHERE user_id=?', (student_id,)).fetchone()
    conn.close()

    score = 0
    suggestions = []
    certificates = json.loads(profile['certificates']) if profile and profile['certificates'] else []
    if len(certificates) >= 1:
        score += 10
    else:
        suggestions.append("Add at least 1 relevant certificate")

    return {'score': score, 'suggestions': suggestions, 'certificates': certificates}
