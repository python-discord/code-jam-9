create_questions_table = '''
        CREATE TABLE QUESTIONS(
            ID SERIAL PRIMARY KEY,
            TXT TEXT NOT NULL,
            TITLE VARCHAR(100) NOT NULL,
            EXPL TEXT NOT NULL,
            DIFFICULTY SMALLINT NOT NULL,
            IDENT VARCHAR(100) NOT NULL,
            VOTES SMALLINT
        )
    '''
creater_answers_table = '''
    CREATE TABLE ANSWERS(
        ID SERIAL PRIMARY KEY,
        ANSWER TEXT NOT NULL,
        IDENT VARCHAR(100) NOT NULL
    )
'''


# - So we can (a) check user score and (b) avoid showing the same question again:
# - CORRECT_ANSWERS - question ids answered correctly
# - INCORRECT_ANSWERS - question ids answered incorrectly
# - So we can give points for submitted good questions, keep a list of:
# - SUBMITTED_QUESTIONS - questions ids the user has submitted
# - SUBMITTED_ADD_VOTES - question ids the user has voted for, to prevent the user from upvoting multiple times
create_users_table = '''
    CREATE TABLE USERS(
        ID SERIAL PRIMARY KEY,
        USER_NAME VARCHAR(30) NOT NULL,
        CORRECT_ANSWERS TEXT,
        INCORRECT_ANSWERS TEXT,
        SUBMITTED_QUESTIONS TEXT,
        SUBMITTED_ADD_VOTES TEXT,
        IDENT VARCHAR(100) NOT NULL
    )
'''
