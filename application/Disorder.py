class Disorder:
    def __init__(self, name, file_name):
        self.name = name
        self.sessions = {}
        self.file_name = file_name

    def add_session(self, session_number, questions):
        self.sessions[session_number] = questions

    def get_session_questions(self, session_number):
        return self.sessions.get(session_number)
