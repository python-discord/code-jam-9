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


# Each user have a list of:
# - FIXME: questions ids the user has added (so we can go through all and check the number of votes)
# - So we can (a) check user score and (b) avoid showing the same question again
# - question ids answered correctly
# - question ids answered incorrectly
create_users_table = '''
    CREATE TABLE USERS(
        ID SERIAL PRIMARY KEY,
        USER_NAME VARCHAR(30) NOT NULL,
        CORRECT_ANSWERS TEXT,
        INCORRECT_ANSWERS TEXT,
        IDENT VARCHAR(100) NOT NULL
    )
'''
