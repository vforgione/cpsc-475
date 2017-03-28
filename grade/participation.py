import codecs
import csv
from typing import List


class Participation:
    def __init__(self, student: str, rc_and_p: int, sprint_value: int, comments: str):
        self.student: str = student
        self.rc_and_p: int = rc_and_p
        self.sprint_value: int = sprint_value
        self.comments: str = comments


def read_participation_csv(filename) -> List[Participation]:
    student_participation: List[Participation] = []

    with codecs.open(filename, mode='r', encoding='utf8') as fh:
        reader = csv.reader(fh, delimiter=',')
        for row in reader:
            student = row[0]
            rc_and_p = int(row[1])
            value = int(row[2])
            try:
                comments = row[3]
            except IndexError:
                comments = ''
            student_participation.append(Participation(student, rc_and_p, value, comments))

    return student_participation


if __name__ == '__main__':
    import sys
    fname = sys.argv[1]
    for sp in read_participation_csv(fname):
        print(f'{sp.student}: {sp.comments}')
