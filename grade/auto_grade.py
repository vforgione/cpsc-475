from argparse import ArgumentParser
from collections import defaultdict
from typing import List

from participation import Participation, read_participation_csv
from prs import PrLoad, read_pr_csv
from tasks import TaskLoad, read_tasks_csv


MINIMUM_COMPLETED_TASK_POINTS = 720

TASK_WEIGHT = 34
PR_WEIGHT = 33
PARTICIPATION_WEIGHT = 33

EXPECTED_RC_AND_P = 8


class Student:
    def __init__(self, name: str, tasks: TaskLoad, prs: PrLoad, participation: Participation, avg_completion: float):
        self.name: str = name
        self.tasks: TaskLoad = tasks
        self.prs: PrLoad = prs
        self.participation: Participation = participation
        self.avg_completion: float = avg_completion

    @property
    def task_value(self) -> float:
        rate = self.tasks.close_rate
        multiplier = self.tasks.closed_task_points / self.avg_completion
        effective_rate = rate * multiplier
        return effective_rate * TASK_WEIGHT

    @property
    def pr_value(self) -> float:
        return self.prs.merge_rate * PR_WEIGHT

    @property
    def participation_value(self) -> float:
        rc_and_p = (self.participation.rc_and_p / EXPECTED_RC_AND_P) * 100
        part_value = (rc_and_p * 0.25) + (self.participation.sprint_value * 0.75)
        part_decimal = part_value / 100
        return part_decimal * PARTICIPATION_WEIGHT

    @property
    def individual_grade(self):
        return self.task_value + self.pr_value + self.participation_value

    def get_cohort_grade(self, avl_grade: float) -> float:
        indy = self.individual_grade
        if indy >= 90:
            return avl_grade

        mod = indy % 10
        if mod < 5:
            nearest = int(indy / 10) * 10
        else:
            nearest = int((indy + 10) / 10) * 10

        rate = nearest / 100
        return avl_grade * rate


def main(participation_filename, pr_filename, task_filename):
    participations: List[Participation] = read_participation_csv(participation_filename)
    prs: List[PrLoad] = read_pr_csv(pr_filename)
    tasks: List[TaskLoad] = read_tasks_csv(task_filename)

    sum_completed = sum(task.closed_task_points for task in tasks)
    avg_completed = sum_completed / len(tasks)
    avg_completion = max([avg_completed, MINIMUM_COMPLETED_TASK_POINTS])

    _students = defaultdict(dict)
    for part in participations:
        name = part.student
        _students[name]['participation'] = part
    for pr_load in prs:
        _students[pr_load.creator]['prs'] = pr_load
    for task_load in tasks:
        _students[task_load.assignee]['tasks'] = task_load

    cohort: List[Student] = []
    for name, kwargs in _students.items():
        if 'tasks' not in kwargs:
            kwargs['tasks'] = TaskLoad(name)
        if 'prs' not in kwargs:
            kwargs['prs'] = PrLoad(name)
        if 'participation' not in kwargs:
            kwargs['participation'] = Participation(name, 0, 0, '')
        kwargs['avg_completion'] = avg_completion
        student = Student(name, **kwargs)
        cohort.append(student)

    cohort_total_task_points = sum(student.tasks.total_points for student in cohort)
    cohort_total_closed_points = sum(student.tasks.closed_task_points for student in cohort)
    cohort_close_rate = cohort_total_closed_points / cohort_total_task_points
    cohort_task_value = cohort_close_rate * 50

    cohort_total_prs_opened = sum(student.prs.total_prs for student in cohort)
    cohort_total_merged_prs = sum(student.prs.merged_prs for student in cohort)
    cohort_pr_merge_rate = cohort_total_merged_prs / cohort_total_prs_opened
    cohort_pr_value = cohort_pr_merge_rate * 50

    maximum_available_cohort_grade = cohort_task_value + cohort_pr_value

    for student in cohort:
        print(f'{student.name}')
        print(f'Individual Grade: {student.individual_grade}')
        group_grade = student.get_cohort_grade(maximum_available_cohort_grade)
        print(f'Group Grade: {group_grade}')
        print('Breakdown:')
        print('  Tasks:')
        print(f'    Total Points: {student.tasks.total_points}')
        print(f'    Closed Points: {student.tasks.closed_task_points}')
        print(f'    Grp Avg Closed Points: {avg_completion}')
        print(f'      Task Value: {student.task_value}')
        print(f'      Pr Value: {student.pr_value}')
        print(f'      Participation Value: {student.participation_value}')
        print('  PRs:')
        print(f'    Total PRs: {student.prs.total_prs}')
        print(f'    Total PRs: {student.prs.merged_prs}')
        print('  Group:')
        print(f'    Max Avl Grade: {maximum_available_cohort_grade}')
        print(student.participation.comments)
        print('\n')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--participation')
    parser.add_argument('-t', '--tasks')
    parser.add_argument('-r', '--prs')
    args = parser.parse_args()

    main(args.participation, args.prs, args.tasks)
